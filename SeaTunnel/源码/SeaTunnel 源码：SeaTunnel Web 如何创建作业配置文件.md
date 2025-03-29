


```java
public String generateJobConfig(Long jobId, List<JobTask> tasks, List<JobLine> lines, String envStr, JobExecParam executeParam) {
        checkSceneMode(tasks);
        BusinessMode businessMode = BusinessMode.valueOf(jobDefinitionDao.getJob(jobId).getJobType());
        Config envConfig = filterEmptyValue(ConfigFactory.parseString(envStr));
        JobUtils.updateDataSource(executeParam, tasks);

        Map<String, List<Config>> sourceMap = new LinkedHashMap<>();
        Map<String, List<Config>> transformMap = new LinkedHashMap<>();
        Map<String, List<Config>> sinkMap = new LinkedHashMap<>();
        Map<String, JobLine> inputLines =
                lines.stream()
                        .collect(
                                Collectors.toMap(
                                        JobLine::getInputPluginId,
                                        Function.identity(),
                                        (existing, replacement) -> existing));
        Map<String, JobLine> targetLines =
                lines.stream()
                        .collect(Collectors.toMap(JobLine::getTargetPluginId, Function.identity()));

        for (JobTask task : tasks) {
            PluginType pluginType = PluginType.valueOf(task.getType().toUpperCase(Locale.ROOT));
            try {
                String pluginId = task.getPluginId();
                OptionRule optionRule =
                        connectorCache.getOptionRule(pluginType.getType(), task.getConnectorType());
                Config config =
                        filterEmptyValue(
                                parseConfigWithOptionRule(
                                        pluginType,
                                        task.getConnectorType(),
                                        task.getConfig(),
                                        optionRule));
                switch (pluginType) {
                    case SOURCE:
                        if (inputLines.containsKey(pluginId)) {
                            config =
                                    addTableName(
                                            CommonOptions.RESULT_TABLE_NAME.key(),
                                            inputLines.get(pluginId),
                                            config);
                            if (!sourceMap.containsKey(task.getConnectorType())) {
                                sourceMap.put(task.getConnectorType(), new ArrayList<>());
                            }

                            if (businessMode.equals(BusinessMode.DATA_REPLICA)) {
                                config =
                                        config.withValue(
                                                DAG_PARSING_MODE,
                                                ConfigValueFactory.fromAnyRef(
                                                        ParsingMode.MULTIPLEX.name()));
                            }

                            if (task.getSceneMode()
                                    .toUpperCase()
                                    .equals(SceneMode.SPLIT_TABLE.name())) {
                                config =
                                        config.withValue(
                                                DAG_PARSING_MODE,
                                                ConfigValueFactory.fromAnyRef(
                                                        ParsingMode.SHARDING.name()));
                            }

                            Config mergeConfig =
                                    mergeTaskConfig(
                                            task,
                                            pluginType,
                                            task.getConnectorType(),
                                            businessMode,
                                            config,
                                            optionRule);
                            sourceMap
                                    .get(task.getConnectorType())
                                    .add(filterEmptyValue(mergeConfig));
                        }
                        break;
                    case TRANSFORM:
                        if (!inputLines.containsKey(pluginId)
                                && !targetLines.containsKey(pluginId)) {
                            break;
                        }
                        if (inputLines.containsKey(pluginId)) {
                            config =
                                    addTableName(
                                            CommonOptions.RESULT_TABLE_NAME.key(),
                                            inputLines.get(pluginId),
                                            config);
                        }
                        if (targetLines.containsKey(pluginId)) {
                            config =
                                    addTableName(
                                            CommonOptions.SOURCE_TABLE_NAME.key(),
                                            targetLines.get(pluginId),
                                            config);
                        }
                        if (!transformMap.containsKey(task.getConnectorType())) {
                            transformMap.put(task.getConnectorType(), new ArrayList<>());
                        }
                        List<TableSchemaReq> inputSchemas = findInputSchemas(tasks, lines, task);
                        Config transformConfig = buildTransformConfig(task, config, inputSchemas);
                        transformMap
                                .get(task.getConnectorType())
                                .add(filterEmptyValue(transformConfig));
                        break;
                    case SINK:
                        if (targetLines.containsKey(pluginId)) {
                            config =
                                    addTableName(
                                            CommonOptions.SOURCE_TABLE_NAME.key(),
                                            targetLines.get(pluginId),
                                            config);
                            if (!sinkMap.containsKey(task.getConnectorType())) {
                                sinkMap.put(task.getConnectorType(), new ArrayList<>());
                            }
                            Config mergeConfig =
                                    mergeTaskConfig(
                                            task,
                                            pluginType,
                                            task.getConnectorType(),
                                            businessMode,
                                            config,
                                            optionRule);

                            sinkMap.get(task.getConnectorType()).add(filterEmptyValue(mergeConfig));
                        }
                        break;
                    default:
                        throw new SeatunnelException(
                                SeatunnelErrorEnum.UNSUPPORTED_CONNECTOR_TYPE,
                                task.getType().toUpperCase());
                }
            } catch (SeatunnelException e) {
                log.error(ExceptionUtils.getMessage(e));
                throw e;
            } catch (Exception e) {
                throw new SeatunnelException(
                        SeatunnelErrorEnum.ERROR_CONFIG,
                        String.format(
                                "Plugin Type: %s, Connector Type: %s, Error Info: %s",
                                pluginType, task.getConnectorType(), ExceptionUtils.getMessage(e)));
            }
        }
        String sources = "";
        if (sourceMap.size() > 0) {
            sources = getConnectorConfig(sourceMap);
        }

        String transforms = "";
        if (transformMap.size() > 0) {
            transforms = getConnectorConfig(transformMap);
        }

        String sinks = "";
        if (sinkMap.size() > 0) {
            sinks = getConnectorConfig(sinkMap);
        }

        if (!encryptionConfig.getType().equals(ENCRYPTION_TYPE_NONE)) {
            envConfig =
                    envConfig.withValue(
                            ENCRYPTION_IDENTIFIER_KEY,
                            ConfigValueFactory.fromAnyRef(encryptionConfig.getType()));
        }

        String env =
                envConfig
                        .root()
                        .render(
                                ConfigRenderOptions.defaults()
                                        .setJson(false)
                                        .setComments(false)
                                        .setOriginComments(false));
        String jobConfig = SeaTunnelConfigUtil.generateConfig(env, sources, transforms, sinks);
        return JobUtils.replaceJobConfigPlaceholders(jobConfig, executeParam);
    }
```
