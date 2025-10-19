

## 1. 架构

```java
public abstract class TwoPhaseCommitSinkFunction<IN, TXN, CONTEXT> extends RichSinkFunction<IN>
        implements CheckpointedFunction, CheckpointListener {

    // -----------------------------------------------------------------------------------------------------------------
    // 实现 CheckpointListener 接口重写 notifyCheckpointComplete 方法

    @Override
    public void notifyCheckpointComplete(long l) throws Exception {

    }

    @Override
    public void notifyCheckpointAborted(long checkpointId) {

    }

    // -----------------------------------------------------------------------------------------------------------------
    // 实现 CheckpointedFunction 接口重写 snapshotState 和 initializeState 方法

    @Override
    public void snapshotState(FunctionSnapshotContext context) throws Exception {

    }

    @Override
    public void initializeState(FunctionInitializationContext context) throws Exception {

    }

    // -----------------------------------------------------------------------------------------------------------------
    // 实现 RichSinkFunction 接口重写 invoke 方法

    @Override
    public void invoke(IN value) throws Exception {
        super.invoke(value);
    }

    @Override
    public void invoke(IN value, Context context) throws Exception {
        super.invoke(value, context);
    }
}
```



```java
protected abstract void invoke(TXN transaction, IN value, Context context) throws Exception;

/**
 * Method that starts a new transaction.
 *
 * @return newly created transaction.
 */
protected abstract TXN beginTransaction() throws Exception;

/**
 * Pre commit previously created transaction. Pre commit must make all of the necessary steps to
 * prepare the transaction for a commit that might happen in the future. After this point the
 * transaction might still be aborted, but underlying implementation must ensure that commit
 * calls on already pre committed transactions will always succeed.
 *
 * <p>Usually implementation involves flushing the data.
 */
protected abstract void preCommit(TXN transaction) throws Exception;

/**
 * Commit a pre-committed transaction. If this method fail, Flink application will be restarted
 * and {@link TwoPhaseCommitSinkFunction#recoverAndCommit(Object)} will be called again for the
 * same transaction.
 */
protected abstract void commit(TXN transaction);

/**
 * Invoked on recovered transactions after a failure. User implementation must ensure that this
 * call will eventually succeed. If it fails, Flink application will be restarted and it will be
 * invoked again. If it does not succeed eventually, a data loss will occur. Transactions will
 * be recovered in an order in which they were created.
 */
protected void recoverAndCommit(TXN transaction) {
    commit(transaction);
}

/** Abort a transaction. */
protected abstract void abort(TXN transaction);

/** Abort a transaction that was rejected by a coordinator after a failure. */
protected void recoverAndAbort(TXN transaction) {
    abort(transaction);
}

/**
 * Callback for subclasses which is called after restoring (each) user context.
 *
 * @param handledTransactions transactions which were already committed or aborted and do not
 *     need further handling
 */
protected void finishRecoveringContext(Collection<TXN> handledTransactions) {}
```

## 2. 核心工作机制

### 2.1 快照管理

#### 2.1.1 snapshotState

```java
public void snapshotState(FunctionSnapshotContext context) throws Exception {
    // this is like the pre-commit of a 2-phase-commit transaction
    // we are ready to commit and remember the transaction

    checkState(
            currentTransactionHolder != null,
            "bug: no transaction object when performing state snapshot");

    long checkpointId = context.getCheckpointId();
    LOG.debug(
            "{} - checkpoint {} triggered, flushing transaction '{}'",
            name(),
            context.getCheckpointId(),
            currentTransactionHolder);

    preCommit(currentTransactionHolder.handle);
    pendingCommitTransactions.put(checkpointId, currentTransactionHolder);
    LOG.debug("{} - stored pending transactions {}", name(), pendingCommitTransactions);

    currentTransactionHolder = beginTransactionInternal();
    LOG.debug("{} - started new transaction '{}'", name(), currentTransactionHolder);

    state.clear();
    state.add(
            new State<>(
                    this.currentTransactionHolder,
                    new ArrayList<>(pendingCommitTransactions.values()),
                    userContext));
}
```

#### 2.1.2 initializeState

```java
@Override
public void initializeState(FunctionInitializationContext context) throws Exception {
    // when we are restoring state with pendingCommitTransactions, we don't really know whether
    // the
    // transactions were already committed, or whether there was a failure between
    // completing the checkpoint on the master, and notifying the writer here.

    // (the common case is actually that is was already committed, the window
    // between the commit on the master and the notification here is very small)

    // it is possible to not have any transactions at all if there was a failure before
    // the first completed checkpoint, or in case of a scale-out event, where some of the
    // new task do not have and transactions assigned to check)

    // we can have more than one transaction to check in case of a scale-in event, or
    // for the reasons discussed in the 'notifyCheckpointComplete()' method.

    state = context.getOperatorStateStore().getListState(stateDescriptor);

    boolean recoveredUserContext = false;
    if (context.isRestored()) {
        LOG.info("{} - restoring state", name());
        for (State<TXN, CONTEXT> operatorState : state.get()) {
            userContext = operatorState.getContext();
            List<TransactionHolder<TXN>> recoveredTransactions =
                    operatorState.getPendingCommitTransactions();
            List<TXN> handledTransactions = new ArrayList<>(recoveredTransactions.size() + 1);
            for (TransactionHolder<TXN> recoveredTransaction : recoveredTransactions) {
                // If this fails to succeed eventually, there is actually data loss
                recoverAndCommitInternal(recoveredTransaction);
                handledTransactions.add(recoveredTransaction.handle);
                LOG.info("{} committed recovered transaction {}", name(), recoveredTransaction);
            }

            {
                TXN transaction = operatorState.getPendingTransaction().handle;
                recoverAndAbort(transaction);
                handledTransactions.add(transaction);
                LOG.info(
                        "{} aborted recovered transaction {}",
                        name(),
                        operatorState.getPendingTransaction());
            }

            if (userContext.isPresent()) {
                finishRecoveringContext(handledTransactions);
                recoveredUserContext = true;
            }
        }
    }

    // if in restore we didn't get any userContext or we are initializing from scratch
    if (!recoveredUserContext) {
        LOG.info("{} - no state to restore", name());

        userContext = initializeUserContext();
    }
    this.pendingCommitTransactions.clear();

    currentTransactionHolder = beginTransactionInternal();
    LOG.debug("{} - started new transaction '{}'", name(), currentTransactionHolder);
}
```

### 2.2 快照完成通知

```java
@Override
public final void notifyCheckpointComplete(long checkpointId) throws Exception {
    // the following scenarios are possible here
    //
    //  (1) there is exactly one transaction from the latest checkpoint that
    //      was triggered and completed. That should be the common case.
    //      Simply commit that transaction in that case.
    //
    //  (2) there are multiple pending transactions because one previous
    //      checkpoint was skipped. That is a rare case, but can happen
    //      for example when:
    //
    //        - the master cannot persist the metadata of the last
    //          checkpoint (temporary outage in the storage system) but
    //          could persist a successive checkpoint (the one notified here)
    //
    //        - other tasks could not persist their status during
    //          the previous checkpoint, but did not trigger a failure because they
    //          could hold onto their state and could successfully persist it in
    //          a successive checkpoint (the one notified here)
    //
    //      In both cases, the prior checkpoint never reach a committed state, but
    //      this checkpoint is always expected to subsume the prior one and cover all
    //      changes since the last successful one. As a consequence, we need to commit
    //      all pending transactions.
    //
    //  (3) Multiple transactions are pending, but the checkpoint complete notification
    //      relates not to the latest. That is possible, because notification messages
    //      can be delayed (in an extreme case till arrive after a succeeding checkpoint
    //      was triggered) and because there can be concurrent overlapping checkpoints
    //      (a new one is started before the previous fully finished).
    //
    // ==> There should never be a case where we have no pending transaction here
    //

    Iterator<Map.Entry<Long, TransactionHolder<TXN>>> pendingTransactionIterator =
            pendingCommitTransactions.entrySet().iterator();
    Throwable firstError = null;

    while (pendingTransactionIterator.hasNext()) {
        Map.Entry<Long, TransactionHolder<TXN>> entry = pendingTransactionIterator.next();
        Long pendingTransactionCheckpointId = entry.getKey();
        TransactionHolder<TXN> pendingTransaction = entry.getValue();
        if (pendingTransactionCheckpointId > checkpointId) {
            continue;
        }

        LOG.info(
                "{} - checkpoint {} complete, committing transaction {} from checkpoint {}",
                name(),
                checkpointId,
                pendingTransaction,
                pendingTransactionCheckpointId);

        logWarningIfTimeoutAlmostReached(pendingTransaction);
        try {
            commit(pendingTransaction.handle);
        } catch (Throwable t) {
            if (firstError == null) {
                firstError = t;
            }
        }

        LOG.debug("{} - committed checkpoint transaction {}", name(), pendingTransaction);

        pendingTransactionIterator.remove();
    }

    if (firstError != null) {
        throw new FlinkRuntimeException(
                "Committing one of transactions failed, logging first encountered failure",
                firstError);
    }
}
```

### 2.3 invoke

```java
@Override
public final void invoke(IN value) throws Exception {}

@Override
public final void invoke(IN value, Context context) throws Exception {
    invoke(currentTransactionHolder.handle, value, context);
}
```
