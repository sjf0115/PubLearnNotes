
https://blog.csdn.net/qq_21383435/article/details/125453087?spm=1001.2101.3001.6661.1&utm_medium=distribute.pc_relevant_t0.none-task-blog-2%7Edefault%7EBlogCommendFromBaidu%7EPaidSort-1-125453087-blog-123864487.235%5Ev43%5Epc_blog_bottom_relevance_base3&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-2%7Edefault%7EBlogCommendFromBaidu%7EPaidSort-1-125453087-blog-123864487.235%5Ev43%5Epc_blog_bottom_relevance_base3&utm_relevant_index=1
```java
public SnapshotResult<KeyedStateHandle> get(CloseableRegistry snapshotCloseableRegistry) throws Exception {
      boolean completed = false;
      SnapshotResult<StreamStateHandle> metaStateHandle = null;
      Map<StateHandleID, StreamStateHandle> sstFiles = new HashMap();
      HashMap miscFiles = new HashMap();
      boolean var15 = false;

      SnapshotResult var18;
      try {
          var15 = true;
          metaStateHandle = this.materializeMetaData(snapshotCloseableRegistry);
          Preconditions.checkNotNull(metaStateHandle, "Metadata was not properly created.");
          Preconditions.checkNotNull(metaStateHandle.getJobManagerOwnedSnapshot(), "Metadata for job manager was not properly created.");
          this.uploadSstFiles(sstFiles, miscFiles, snapshotCloseableRegistry);
          synchronized(RocksIncrementalSnapshotStrategy.this.materializedSstFiles) {
              RocksIncrementalSnapshotStrategy.this.materializedSstFiles.put(this.checkpointId, sstFiles.keySet());
          }

          IncrementalRemoteKeyedStateHandle jmIncrementalKeyedStateHandle = new IncrementalRemoteKeyedStateHandle(RocksIncrementalSnapshotStrategy.this.backendUID, RocksIncrementalSnapshotStrategy.this.keyGroupRange, this.checkpointId, sstFiles, miscFiles, (StreamStateHandle)metaStateHandle.getJobManagerOwnedSnapshot());
          DirectoryStateHandle directoryStateHandle = this.localBackupDirectory.completeSnapshotAndGetHandle();
          SnapshotResult snapshotResult;
          if (directoryStateHandle != null && metaStateHandle.getTaskLocalSnapshot() != null) {
              IncrementalLocalKeyedStateHandle localDirKeyedStateHandle = new IncrementalLocalKeyedStateHandle(RocksIncrementalSnapshotStrategy.this.backendUID, this.checkpointId, directoryStateHandle, RocksIncrementalSnapshotStrategy.this.keyGroupRange, (StreamStateHandle)metaStateHandle.getTaskLocalSnapshot(), sstFiles.keySet());
              snapshotResult = SnapshotResult.withLocalState(jmIncrementalKeyedStateHandle, localDirKeyedStateHandle);
          } else {
              snapshotResult = SnapshotResult.of(jmIncrementalKeyedStateHandle);
          }

          completed = true;
          var18 = snapshotResult;
          var15 = false;
      } finally {
          if (var15) {
              if (!completed) {
                  List<StateObject> statesToDiscard = new ArrayList(1 + miscFiles.size() + sstFiles.size());
                  statesToDiscard.add(metaStateHandle);
                  statesToDiscard.addAll(miscFiles.values());
                  statesToDiscard.addAll(sstFiles.values());
                  this.cleanupIncompleteSnapshot(statesToDiscard);
              }

          }
      }

```
