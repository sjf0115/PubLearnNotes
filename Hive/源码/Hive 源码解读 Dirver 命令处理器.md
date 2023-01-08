
## 1. run

```java
public CommandProcessorResponse run(String command, boolean alreadyCompiled) throws CommandNeedRetryException {
    CommandProcessorResponse cpr = runInternal(command, alreadyCompiled);
    ...
}
```

```java
    if(cpr.getResponseCode() == 0) {
      return cpr;
    }
    SessionState ss = SessionState.get();
    if(ss == null) {
      return cpr;
    }
    MetaDataFormatter mdf = MetaDataFormatUtils.getFormatter(ss.getConf());
    if(!(mdf instanceof JsonMetaDataFormatter)) {
      return cpr;
    }
    try {
      if(downstreamError == null) {
        mdf.error(ss.out, errorMessage, cpr.getResponseCode(), SQLState);
        return cpr;
      }
      ErrorMsg canonicalErr = ErrorMsg.getErrorMsg(cpr.getResponseCode());
      if(canonicalErr != null && canonicalErr != ErrorMsg.GENERIC_ERROR) {
        mdf.error(ss.out, errorMessage, cpr.getResponseCode(), SQLState, null);
        return cpr;
      }
      if(downstreamError instanceof HiveException) {
        HiveException rc = (HiveException) downstreamError;
        mdf.error(ss.out, errorMessage,
                rc.getCanonicalErrorMsg().getErrorCode(), SQLState,
                rc.getCanonicalErrorMsg() == ErrorMsg.GENERIC_ERROR ?
                        org.apache.hadoop.util.StringUtils.stringifyException(rc)
                        : null);
      }
      else {
        ErrorMsg canonicalMsg =
                ErrorMsg.getErrorMsg(downstreamError.getMessage());
        mdf.error(ss.out, errorMessage, canonicalMsg.getErrorCode(),
                SQLState, org.apache.hadoop.util.StringUtils.
                stringifyException(downstreamError));
      }
    } catch(HiveException ex) {
      console.printError("Unable to JSON-encode the error",
              org.apache.hadoop.util.StringUtils.stringifyException(ex));
    }
    return cpr;
}
```

## 2. compileInternal

```java
private CommandProcessorResponse runInternal(String command, boolean alreadyCompiled) throws CommandNeedRetryException {
    errorMessage = null;
    SQLState = null;
    downstreamError = null;
    lDrvState.stateLock.lock();
    try {
      if (alreadyCompiled) {
        if (lDrvState.driverState == DriverState.COMPILED) {
          lDrvState.driverState = DriverState.EXECUTING;
        } else {
          errorMessage = "FAILED: Precompiled query has been cancelled or closed.";
          console.printError(errorMessage);
          return createProcessorResponse(12);
        }
      } else {
        lDrvState.driverState = DriverState.COMPILING;
      }
    } finally {
      lDrvState.stateLock.unlock();
    }


    boolean isFinishedWithError = true;
    try {
      HiveDriverRunHookContext hookContext = new HiveDriverRunHookContextImpl(conf,
          alreadyCompiled ? ctx.getCmd() : command);
      // Get all the driver run hooks and pre-execute them.
      List<HiveDriverRunHook> driverRunHooks;
      try {
        driverRunHooks = getHooks(HiveConf.ConfVars.HIVE_DRIVER_RUN_HOOKS, HiveDriverRunHook.class);
        for (HiveDriverRunHook driverRunHook : driverRunHooks) {
            driverRunHook.preDriverRun(hookContext);
        }
      } catch (Exception e) {
        errorMessage = "FAILED: Hive Internal Error: " + Utilities.getNameMessage(e);
        SQLState = ErrorMsg.findSQLState(e.getMessage());
        downstreamError = e;
        console.printError(errorMessage + "\n"
            + org.apache.hadoop.util.StringUtils.stringifyException(e));
        return createProcessorResponse(12);
      }

      PerfLogger perfLogger = null;

      int ret;
      if (!alreadyCompiled) {
        // compile internal will automatically reset the perf logger
        ret = compileInternal(command, true);
        // then we continue to use this perf logger
        perfLogger = SessionState.getPerfLogger();
        if (ret != 0) {
          return createProcessorResponse(ret);
        }
      } else {
        // reuse existing perf logger.
        perfLogger = SessionState.getPerfLogger();
        // Since we're reusing the compiled plan, we need to update its start time for current run
        plan.setQueryStartTime(perfLogger.getStartTime(PerfLogger.DRIVER_RUN));
      }
      // the reason that we set the txn manager for the cxt here is because each
      // query has its own ctx object. The txn mgr is shared across the
      // same instance of Driver, which can run multiple queries.
      HiveTxnManager txnManager = SessionState.get().getTxnMgr();
      ctx.setHiveTxnManager(txnManager);

      boolean startTxnImplicitly = false;
      {
        //this block ensures op makes sense in given context, e.g. COMMIT is valid only if txn is open
        //DDL is not allowed in a txn, etc.
        //an error in an open txn does a rollback of the txn
        if (txnManager.isTxnOpen() && !plan.getOperation().isAllowedInTransaction()) {
          assert !txnManager.getAutoCommit() : "didn't expect AC=true";
          return rollback(new CommandProcessorResponse(12, ErrorMsg.OP_NOT_ALLOWED_IN_TXN, null,
            plan.getOperationName(), Long.toString(txnManager.getCurrentTxnId())));
        }
        if(!txnManager.isTxnOpen() && plan.getOperation().isRequiresOpenTransaction()) {
          return rollback(new CommandProcessorResponse(12, ErrorMsg.OP_NOT_ALLOWED_WITHOUT_TXN, null, plan.getOperationName()));
        }
        if(!txnManager.isTxnOpen() && plan.getOperation() == HiveOperation.QUERY && !txnManager.getAutoCommit()) {
          //this effectively makes START TRANSACTION optional and supports JDBC setAutoCommit(false) semantics
          //also, indirectly allows DDL to be executed outside a txn context
          startTxnImplicitly = true;
        }
        if(txnManager.getAutoCommit() && plan.getOperation() == HiveOperation.START_TRANSACTION) {
          return rollback(new CommandProcessorResponse(12, ErrorMsg.OP_NOT_ALLOWED_IN_AUTOCOMMIT, null, plan.getOperationName()));
        }
      }
      if(plan.getOperation() == HiveOperation.SET_AUTOCOMMIT) {
        try {
          if(plan.getAutoCommitValue() && !txnManager.getAutoCommit()) {
            /*here, if there is an open txn, we want to commit it; this behavior matches
            * https://docs.oracle.com/javase/6/docs/api/java/sql/Connection.html#setAutoCommit(boolean)*/
            releaseLocksAndCommitOrRollback(true, null);
            txnManager.setAutoCommit(true);
          }
          else if(!plan.getAutoCommitValue() && txnManager.getAutoCommit()) {
            txnManager.setAutoCommit(false);
          }
          else {/*didn't change autoCommit value - no-op*/}
        }
        catch(LockException e) {
          return handleHiveException(e, 12);
        }
      }

      if (requiresLock()) {
        // a checkpoint to see if the thread is interrupted or not before an expensive operation
        if (isInterrupted()) {
          ret = handleInterruption("at acquiring the lock.");
        } else {
          ret = acquireLocksAndOpenTxn(startTxnImplicitly);
        }
        if (ret != 0) {
          return rollback(createProcessorResponse(ret));
        }
      }
      ret = execute(true);
      if (ret != 0) {
        //if needRequireLock is false, the release here will do nothing because there is no lock
        return rollback(createProcessorResponse(ret));
      }

      //if needRequireLock is false, the release here will do nothing because there is no lock
      try {
        if(txnManager.getAutoCommit() || plan.getOperation() == HiveOperation.COMMIT) {
          releaseLocksAndCommitOrRollback(true, null);
        }
        else if(plan.getOperation() == HiveOperation.ROLLBACK) {
          releaseLocksAndCommitOrRollback(false, null);
        }
        else {
          //txn (if there is one started) is not finished
        }
      } catch (LockException e) {
        return handleHiveException(e, 12);
      }

      perfLogger.PerfLogEnd(CLASS_NAME, PerfLogger.DRIVER_RUN);
      queryDisplay.setPerfLogStarts(QueryDisplay.Phase.EXECUTION, perfLogger.getStartTimes());
      queryDisplay.setPerfLogEnds(QueryDisplay.Phase.EXECUTION, perfLogger.getEndTimes());

      // Take all the driver run hooks and post-execute them.
      try {
        for (HiveDriverRunHook driverRunHook : driverRunHooks) {
            driverRunHook.postDriverRun(hookContext);
        }
      } catch (Exception e) {
        errorMessage = "FAILED: Hive Internal Error: " + Utilities.getNameMessage(e);
        SQLState = ErrorMsg.findSQLState(e.getMessage());
        downstreamError = e;
        console.printError(errorMessage + "\n"
            + org.apache.hadoop.util.StringUtils.stringifyException(e));
        return createProcessorResponse(12);
      }
      isFinishedWithError = false;
      return createProcessorResponse(ret);
    } finally {
      if (isInterrupted()) {
        closeInProcess(true);
      } else {
        // only release the related resources ctx, driverContext as normal
        releaseResources();
      }
      lDrvState.stateLock.lock();
      try {
        if (lDrvState.driverState == DriverState.INTERRUPT) {
          lDrvState.driverState = DriverState.ERROR;
        } else {
          lDrvState.driverState = isFinishedWithError ? DriverState.ERROR : DriverState.EXECUTED;
        }
      } finally {
        lDrvState.stateLock.unlock();
      }
    }
}
```

## 3. execute
