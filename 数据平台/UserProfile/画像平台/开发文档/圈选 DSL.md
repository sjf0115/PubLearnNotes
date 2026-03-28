# 1. 火山引擎

## 1. 用户是/用户不是

### 1.1 群组

- filter: 指定类型
- operation: 操作符
- operationValues: 操作值
- period: 时间周期
  - 对群组而言没有用处

```json
{
  "filter": {
    "property_type": "cohort",
    "property_compose_type": "origin",
    "name": "cohort",
    "show_name": "用户分群"
  },
  "operation": {
    "label": "=",
    "value": "="
  },
  "operationValues": [
    {
      "value": 100025248,
      "label": "【2024】通用培训"
    }
  ],
  "period": {
    "granularity": "day",
    "weekStart": 1,
    "beginTime": {
      "timestamp": 1741104000,
      "amount": 7,
      "unit": "day",
      "hour": 0,
      "tab": 2
    },
    "endTime": {
      "timestamp": 1741622400,
      "amount": 2,
      "unit": "day",
      "hour": 23,
      "tab": 3
    },
    "shortcut": "past_7_day"
  }
}
```

### 1.2 标签

- filter: 指定类型
- operation: 操作符
- operationValues: 操作值
- period: 时间周期
  - 对群组而言没有用处

```json
{
  "filter": {
    "property_compose_type": "origin",
    "property_type": "user_profile",
    "name": "gender",
    "show_name": "性别",
    "preset": true,
    "support_operations": [
      "is_null",
      "is_not_null",
      "=",
      "!=",
      "not_equal_not_contain_null"
    ],
    "value_type": "string",
    "has_property_dict": false
  },
  "operation": {
    "label": "=",
    "alias": "",
    "tip": "=",
    "value": "="
  },
  "operationValues": [
    {
      "value": "male",
      "label": "男"
    }
  ],
  "period": {
    "granularity": "day",
    "weekStart": 1,
    "beginTime": {
      "timestamp": 1741104000,
      "amount": 7,
      "unit": "day",
      "hour": 0,
      "tab": 2
    },
    "endTime": {
      "timestamp": 1741622400,
      "amount": 2,
      "unit": "day",
      "hour": 23,
      "tab": 3
    },
    "shortcut": "past_7_day"
  }
}
```


## 2. 用户做过/用户未做过

- 指标类型
- "events",
- "event_users",
- "events_per_user",
- "uv_per_au",
- "pv_per_au",
- "sum",
- "avg",
- "per_user",
- "pct",
- "pct_t_digest",
- "sum_per_au",
- "min",
- "max",
- "distinct",
- distinct_user_attr"


```json
{
  "event": {
    "event_type": "origin",
    "event_name": "app_launch",
    "show_name": "应用启动",
    "event_id": 246200677,
    "preset": true,
    "support_indicators": [
      "events",
      "event_users",
      "events_per_user",
      "uv_per_au",
      "pv_per_au",
      "sum",
      "avg",
      "per_user",
      "pct",
      "pct_t_digest",
      "sum_per_au",
      "min",
      "max",
      "distinct",
      "distinct_user_attr"
    ],
    "metric": {

    },
    "sub_app_id": null
  },
  "filters": {
    "logic": "and",
    "conditions": [
      {
        "uuid": "58017f68-a907-4a26-8f0a-817c70d00eae",
        "operation": {
          "label": "=",
          "alias": "",
          "tip": "=",
          "value": "="
        },
        "filter": {
          "property_compose_type": "origin",
          "property_type": "event_param",
          "name": "$os_version",
          "show_name": "系统版本",
          "preset": true,
          "support_operations": [
            "is_null",
            "is_not_null",
            "=",
            "!=",
            "not_equal_not_contain_null",
            "contain",
            "not_contain",
            "not_contain_contain_null",
            "custom_contain",
            "match",
            "not_match"
          ],
          "value_type": "string",
          "has_property_dict": false
        },
        "operationValues": [
          {
            "label": null,
            "value": "16.6"
          }
        ]
      }
    ]
  },
  "measure": {
    "indicator": {
      "indicator_type": "events"
    }
  },
  "operation": {
    "label": ">=",
    "value": ">="
  },
  "operationValues": [
    {
      "uuid": "c1f978c6-cc05-4283-a755-eec223d60c2f",
      "label": "1",
      "value": 1
    }
  ],
  "period": {
    "granularity": "day",
    "weekStart": 1,
    "beginTime": {
      "timestamp": 1741104000,
      "amount": 7,
      "unit": "day",
      "hour": 0,
      "tab": 2
    },
    "endTime": {
      "timestamp": 1741622400,
      "amount": 2,
      "unit": "day",
      "hour": 23,
      "tab": 3
    },
    "shortcut": "past_7_day"
  }
}
```

## 3. 依次做过/依次为做过

```json
{
  "events": [
    {
      "uuid": "691a29b4-242a-4b78-8a27-b132bf43727a",
      "event": {
        "event_type": "origin",
        "event_name": "app_launch",
        "show_name": "应用启动",
        "event_id": 246200677,
        "preset": true,
        "support_indicators": [
          "events",
          "count_by_date",
          "event_days",
          "consecutive_date",
          "sum",
          "avg",
          "min",
          "max",
          "distinct"
        ],
        "metric": {

        },
        "sub_app_id": null
      },
      "filters": {
        "logic": "and",
        "conditions": [
          {
            "uuid": "6d70bb9f-91b8-43c2-9347-7d91fc8115ae",
            "filter": {
              "property_compose_type": "origin",
              "property_type": "common_param",
              "name": "os_name",
              "show_name": "操作系统",
              "preset": true,
              "support_operations": [
                "is_null",
                "is_not_null",
                "=",
                "!=",
                "not_equal_not_contain_null",
                "contain",
                "not_contain",
                "not_contain_contain_null",
                "custom_contain",
                "match",
                "not_match"
              ],
              "value_type": "string",
              "has_property_dict": false
            },
            "operation": {
              "label": "=",
              "alias": "",
              "tip": "=",
              "value": "="
            },
            "operationValues": [
              {
                "label": null,
                "value": "ios"
              }
            ]
          }
        ]
      }
    },
    {
      "event": {
        "event_type": "origin",
        "event_name": "goods_order_pay",
        "show_name": "商品订单支付",
        "event_id": 246222252,
        "preset": false,
        "support_indicators": [
          "events",
          "count_by_date",
          "event_days",
          "consecutive_date",
          "sum",
          "avg",
          "min",
          "max",
          "distinct"
        ],
        "metric": {

        },
        "sub_app_id": null
      },
      "filters": {
        "logic": "and",
        "conditions": [
          {
            "uuid": "5c4f1281-7968-40cc-a62a-1ee51ce308b8",
            "filter": {
              "property_compose_type": "origin",
              "property_type": "common_param",
              "name": "app_channel",
              "show_name": "渠道",
              "preset": true,
              "support_operations": [
                "is_null",
                "is_not_null",
                "=",
                "!=",
                "not_equal_not_contain_null",
                "contain",
                "not_contain",
                "not_contain_contain_null",
                "custom_contain",
                "match",
                "not_match"
              ],
              "value_type": "string",
              "has_property_dict": false
            },
            "operation": {
              "label": "=",
              "alias": "",
              "tip": "=",
              "value": "="
            },
            "operationValues": [
              {
                "label": null,
                "value": "抖音视频"
              }
            ]
          }
        ]
      },
      "uuid": "7543fcc4-77fa-4fa8-be04-0403a0993ed2"
    }
  ],
  "period": {
    "granularity": "day",
    "weekStart": 1,
    "beginTime": {
      "timestamp": 1773504000,
      "amount": 7,
      "unit": "day",
      "hour": 0,
      "tab": 2
    },
    "endTime": {
      "timestamp": 1774022400,
      "amount": 2,
      "unit": "day",
      "hour": 23,
      "tab": 3
    },
    "shortcut": "past_7_day"
  }
}
```




show_option:
```
{
  "period": {
    "granularity": "day",
    "weekStart": 1,
    "beginTime": {
      "timestamp": 1741104000,
      "amount": 7,
      "unit": "day",
      "hour": 0,
      "tab": 2
    },
    "endTime": {
      "timestamp": 1741622400,
      "amount": 2,
      "unit": "day",
      "hour": 23,
      "tab": 3
    },
    "shortcut": "past_7_day"
  },
  "conditions": {
    "logic": "or",
    "conditions": [
      {
        "uuid": "6dd84977-c3ee-4849-b32d-9cf7397a20d4",
        "logic": "and",
        "conditions": [
          {
            "uuid": "676c0fc8-6aab-42ed-af78-3de14014205f",
            "type": "profile",
            "event": {
              "event": {
                "event_type": "origin",
                "event_name": "any_event",
                "show_name": "任意事件"
              },
              "filters": {
                "logic": "and",
                "conditions": [

                ]
              },
              "measure": {
                "indicator": {
                  "indicator_type": "events"
                },
                "label": "总次数"
              },
              "operation": {
                "label": "≥",
                "value": ">="
              },
              "operationValues": [
                {
                  "uuid": "243094ea-6dc5-4b1c-987b-0cce27885bf8",
                  "label": "1",
                  "value": 1
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1741104000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1741622400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            },
            "profile": {
              "filter": {
                "property_type": "cohort",
                "property_compose_type": "origin",
                "name": "cohort",
                "show_name": "用户分群"
              },
              "operation": {
                "label": "=",
                "value": "="
              },
              "operationValues": [
                {
                  "value": 100025248,
                  "label": "【2024】通用培训"
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1741104000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1741622400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            },
            "events": {

            }
          },
          {
            "uuid": "658c1e9a-aa70-4468-a1bd-16c6070c7904",
            "type": "event",
            "event": {
              "event": {
                "event_type": "origin",
                "event_name": "app_launch",
                "show_name": "应用启动",
                "event_id": 246200677,
                "preset": true,
                "support_indicators": [
                  "events",
                  "count_by_date",
                  "event_days",
                  "consecutive_date",
                  "sum",
                  "avg",
                  "min",
                  "max",
                  "distinct"
                ],
                "metric": {

                },
                "sub_app_id": null
              },
              "filters": {
                "logic": "and",
                "conditions": [
                  {
                    "uuid": "89ebecb8-777a-4e67-b3bf-2893d84966b7",
                    "operation": {
                      "label": "=",
                      "alias": "",
                      "tip": "=",
                      "value": "="
                    },
                    "filter": {
                      "property_compose_type": "origin",
                      "property_type": "common_param",
                      "name": "platform",
                      "show_name": "平台类型",
                      "preset": true,
                      "support_operations": [
                        "is_null",
                        "is_not_null",
                        "=",
                        "!=",
                        "not_equal_not_contain_null",
                        "contain",
                        "not_contain",
                        "not_contain_contain_null",
                        "custom_contain",
                        "match",
                        "not_match"
                      ],
                      "value_type": "string",
                      "has_property_dict": false
                    },
                    "operationValues": [
                      {
                        "label": null,
                        "value": "ios"
                      }
                    ]
                  }
                ]
              },
              "measure": {
                "indicator": {
                  "indicator_type": "events"
                }
              },
              "operation": {
                "label": ">=",
                "value": ">="
              },
              "operationValues": [
                {
                  "uuid": "45aeb083-ea64-4121-96c3-fd181825d6e6",
                  "label": "1",
                  "value": 1
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1741104000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1741622400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            },
            "profile": {
              "filter": {
                "property_compose_type": "origin",
                "property_type": "user_profile",
                "name": "gender",
                "show_name": "性别",
                "preset": true,
                "support_operations": [
                  "is_null",
                  "is_not_null",
                  "=",
                  "!=",
                  "not_equal_not_contain_null"
                ],
                "value_type": "string",
                "has_property_dict": false
              },
              "operation": {
                "label": "=",
                "alias": "",
                "tip": "=",
                "value": "="
              },
              "operationValues": [
                {
                  "value": "male",
                  "label": "男"
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1741104000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1741622400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            },
            "events": {

            }
          }
        ]
      },
      {
        "uuid": "0fc79397-7402-4fa4-a90e-98b7b50d168d",
        "logic": "and",
        "conditions": [
          {
            "uuid": "67fbc5b4-7323-49ce-abed-5a8b5ef07322",
            "type": "not_profile",
            "event": {
              "event": {
                "event_type": "origin",
                "event_name": "app_launch",
                "show_name": "应用启动",
                "event_id": 246200677,
                "preset": true,
                "support_indicators": [
                  "events",
                  "event_users",
                  "events_per_user",
                  "uv_per_au",
                  "pv_per_au",
                  "sum",
                  "avg",
                  "per_user",
                  "pct",
                  "pct_t_digest",
                  "sum_per_au",
                  "min",
                  "max",
                  "distinct",
                  "distinct_user_attr"
                ],
                "metric": {

                },
                "sub_app_id": null
              },
              "filters": {
                "logic": "and",
                "conditions": [
                  {
                    "uuid": "58017f68-a907-4a26-8f0a-817c70d00eae",
                    "operation": {
                      "label": "=",
                      "alias": "",
                      "tip": "=",
                      "value": "="
                    },
                    "filter": {
                      "property_compose_type": "origin",
                      "property_type": "event_param",
                      "name": "$os_version",
                      "show_name": "系统版本",
                      "preset": true,
                      "support_operations": [
                        "is_null",
                        "is_not_null",
                        "=",
                        "!=",
                        "not_equal_not_contain_null",
                        "contain",
                        "not_contain",
                        "not_contain_contain_null",
                        "custom_contain",
                        "match",
                        "not_match"
                      ],
                      "value_type": "string",
                      "has_property_dict": false
                    },
                    "operationValues": [
                      {
                        "label": null,
                        "value": "16.6"
                      }
                    ]
                  }
                ]
              },
              "measure": {
                "indicator": {
                  "indicator_type": "events"
                }
              },
              "operation": {
                "label": ">=",
                "value": ">="
              },
              "operationValues": [
                {
                  "uuid": "c1f978c6-cc05-4283-a755-eec223d60c2f",
                  "label": "1",
                  "value": 1
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1741104000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1741622400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            },
            "events": {

            },
            "profile": {
              "filter": {
                "property_compose_type": "origin",
                "property_type": "user_profile",
                "name": "user_is_new",
                "show_name": "是否新用户",
                "preset": true,
                "support_operations": [
                  "=",
                  "!="
                ],
                "value_type": "int",
                "has_property_dict": false
              },
              "operation": {
                "label": "=",
                "alias": "",
                "tip": "=",
                "value": "="
              },
              "operationValues": [
                {
                  "label": "新用户",
                  "value": 1
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1773504000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1774022400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            }
          },
          {
            "uuid": "872d65d6-5b61-4d2f-aa13-0bac3ecfefd4",
            "type": "not_event",
            "event": {
              "event": {
                "event_type": "origin",
                "event_name": "app_terminate",
                "show_name": "应用退出",
                "event_id": 246200678,
                "preset": true,
                "support_indicators": [
                  "events",
                  "event_users",
                  "events_per_user",
                  "uv_per_au",
                  "pv_per_au",
                  "sum",
                  "avg",
                  "per_user",
                  "pct",
                  "pct_t_digest",
                  "sum_per_au",
                  "min",
                  "max",
                  "distinct",
                  "distinct_user_attr"
                ],
                "metric": {

                },
                "sub_app_id": null
              },
              "filters": {
                "logic": "and",
                "conditions": [
                  {
                    "uuid": "4221a99f-5af0-4b62-9f2c-b0693ff19c25",
                    "operation": {
                      "label": "=",
                      "alias": "",
                      "tip": "=",
                      "value": "="
                    },
                    "filter": {
                      "property_compose_type": "origin",
                      "property_type": "common_param",
                      "name": "os_name",
                      "show_name": "操作系统",
                      "preset": true,
                      "support_operations": [
                        "is_null",
                        "is_not_null",
                        "=",
                        "!=",
                        "not_equal_not_contain_null",
                        "contain",
                        "not_contain",
                        "not_contain_contain_null",
                        "custom_contain",
                        "match",
                        "not_match"
                      ],
                      "value_type": "string",
                      "has_property_dict": false
                    },
                    "operationValues": [
                      {
                        "label": null,
                        "value": "ios"
                      }
                    ]
                  }
                ]
              },
              "measure": {
                "indicator": {
                  "indicator_type": "events"
                }
              },
              "operation": {
                "label": ">=",
                "value": ">="
              },
              "operationValues": [
                {
                  "uuid": "5191663e-18da-4298-8873-3daa36275302",
                  "label": "1",
                  "value": 1
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1741104000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1741622400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            },
            "events": {

            }
          }
        ]
      },
      {
        "uuid": "a8149b49-a078-485b-b371-dc180528884c",
        "logic": "and",
        "conditions": [
          {
            "uuid": "6e7312c1-64a0-450c-86d6-ca0c8fcfddb3",
            "type": "events",
            "event": {
              "event": null,
              "filters": {
                "logic": "and",
                "conditions": [

                ]
              },
              "measure": {
                "indicator": {
                  "indicator_type": "events"
                },
                "label": "总次数"
              },
              "operation": {
                "label": "≥",
                "value": ">="
              },
              "operationValues": [
                {
                  "uuid": "6ef96582-bcb7-40ec-9097-92f3c0b69dd0",
                  "label": "1",
                  "value": 1
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1773504000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1774022400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            },
            "events": {
              "events": [
                {
                  "uuid": "691a29b4-242a-4b78-8a27-b132bf43727a",
                  "event": {
                    "event_type": "origin",
                    "event_name": "app_launch",
                    "show_name": "应用启动",
                    "event_id": 246200677,
                    "preset": true,
                    "support_indicators": [
                      "events",
                      "count_by_date",
                      "event_days",
                      "consecutive_date",
                      "sum",
                      "avg",
                      "min",
                      "max",
                      "distinct"
                    ],
                    "metric": {

                    },
                    "sub_app_id": null
                  },
                  "filters": {
                    "logic": "and",
                    "conditions": [
                      {
                        "uuid": "6d70bb9f-91b8-43c2-9347-7d91fc8115ae",
                        "filter": {
                          "property_compose_type": "origin",
                          "property_type": "common_param",
                          "name": "os_name",
                          "show_name": "操作系统",
                          "preset": true,
                          "support_operations": [
                            "is_null",
                            "is_not_null",
                            "=",
                            "!=",
                            "not_equal_not_contain_null",
                            "contain",
                            "not_contain",
                            "not_contain_contain_null",
                            "custom_contain",
                            "match",
                            "not_match"
                          ],
                          "value_type": "string",
                          "has_property_dict": false
                        },
                        "operation": {
                          "label": "=",
                          "alias": "",
                          "tip": "=",
                          "value": "="
                        },
                        "operationValues": [
                          {
                            "label": null,
                            "value": "ios"
                          }
                        ]
                      }
                    ]
                  }
                },
                {
                  "event": {
                    "event_type": "origin",
                    "event_name": "goods_order_pay",
                    "show_name": "商品订单支付",
                    "event_id": 246222252,
                    "preset": false,
                    "support_indicators": [
                      "events",
                      "count_by_date",
                      "event_days",
                      "consecutive_date",
                      "sum",
                      "avg",
                      "min",
                      "max",
                      "distinct"
                    ],
                    "metric": {

                    },
                    "sub_app_id": null
                  },
                  "filters": {
                    "logic": "and",
                    "conditions": [
                      {
                        "uuid": "5c4f1281-7968-40cc-a62a-1ee51ce308b8",
                        "filter": {
                          "property_compose_type": "origin",
                          "property_type": "common_param",
                          "name": "app_channel",
                          "show_name": "渠道",
                          "preset": true,
                          "support_operations": [
                            "is_null",
                            "is_not_null",
                            "=",
                            "!=",
                            "not_equal_not_contain_null",
                            "contain",
                            "not_contain",
                            "not_contain_contain_null",
                            "custom_contain",
                            "match",
                            "not_match"
                          ],
                          "value_type": "string",
                          "has_property_dict": false
                        },
                        "operation": {
                          "label": "=",
                          "alias": "",
                          "tip": "=",
                          "value": "="
                        },
                        "operationValues": [
                          {
                            "label": null,
                            "value": "抖音视频"
                          }
                        ]
                      }
                    ]
                  },
                  "uuid": "7543fcc4-77fa-4fa8-be04-0403a0993ed2"
                }
              ],
              "period": {
                "granularity": "day",
                "weekStart": 1,
                "beginTime": {
                  "timestamp": 1773504000,
                  "amount": 7,
                  "unit": "day",
                  "hour": 0,
                  "tab": 2
                },
                "endTime": {
                  "timestamp": 1774022400,
                  "amount": 2,
                  "unit": "day",
                  "hour": 23,
                  "tab": 3
                },
                "shortcut": "past_7_day"
              }
            }
          }
        ]
      }
    ]
  }
}
```
content:
```
{
  "queries": [
    [
      {
        "show_label": "676c0fc8-6aab-42ed-af78-3de14014205f",
        "event_indicator": "events",
        "logic": true,
        "condition": {
          "property_operation": ">",
          "property_values": [
            0
          ]
        },
        "filters": [
          {
            "expression": {
              "logic": "and",
              "conditions": [
                {
                  "property_type": "cohort",
                  "property_name": "cohort",
                  "property_compose_type": "origin",
                  "property_operation": "=",
                  "property_values": [
                    100025248
                  ]
                }
              ]
            }
          }
        ],
        "cohort_condition_type": "profile"
      },
      {
        "show_label": "658c1e9a-aa70-4468-a1bd-16c6070c7904",
        "event_name": "app_launch",
        "event_type": "origin",
        "event_id": 246200677,
        "logic": true,
        "event_indicator": "events",
        "measure_info": {

        },
        "condition": {
          "property_operation": ">=",
          "property_values": [
            1
          ],
          "period": {
            "granularity": "day",
            "type": "past_range",
            "spans": [
              {
                "type": "past",
                "past": {
                  "amount": 7,
                  "unit": "day"
                }
              },
              {
                "type": "past",
                "past": {
                  "amount": 1,
                  "unit": "day"
                }
              }
            ],
            "timezone": "Asia/Shanghai",
            "week_start": 1
          }
        },
        "filters": [
          {
            "expression": {
              "logic": "and",
              "conditions": [
                {
                  "property_type": "common_param",
                  "property_name": "platform",
                  "property_compose_type": "origin",
                  "property_operation": "=",
                  "property_values": [
                    "ios"
                  ]
                }
              ]
            }
          }
        ],
        "cohort_condition_type": "event"
      }
    ],
    [
      {
        "show_label": "67fbc5b4-7323-49ce-abed-5a8b5ef07322",
        "event_indicator": "events",
        "logic": false,
        "condition": {
          "property_operation": ">",
          "property_values": [
            0
          ]
        },
        "filters": [
          {
            "expression": {
              "logic": "and",
              "conditions": [
                {
                  "property_type": "user_profile",
                  "property_name": "user_is_new",
                  "property_compose_type": "origin",
                  "property_operation": "=",
                  "property_values": [
                    1
                  ]
                }
              ]
            }
          }
        ],
        "cohort_condition_type": "not_profile"
      },
      {
        "show_label": "872d65d6-5b61-4d2f-aa13-0bac3ecfefd4",
        "event_name": "app_terminate",
        "event_type": "origin",
        "event_id": 246200678,
        "logic": false,
        "event_indicator": "events",
        "measure_info": {

        },
        "condition": {
          "property_operation": ">=",
          "property_values": [
            1
          ],
          "period": {
            "granularity": "day",
            "type": "past_range",
            "spans": [
              {
                "type": "past",
                "past": {
                  "amount": 7,
                  "unit": "day"
                }
              },
              {
                "type": "past",
                "past": {
                  "amount": 1,
                  "unit": "day"
                }
              }
            ],
            "timezone": "Asia/Shanghai",
            "week_start": 1
          }
        },
        "filters": [
          {
            "expression": {
              "logic": "and",
              "conditions": [
                {
                  "property_type": "common_param",
                  "property_name": "os_name",
                  "property_compose_type": "origin",
                  "property_operation": "=",
                  "property_values": [
                    "ios"
                  ]
                }
              ]
            }
          }
        ],
        "cohort_condition_type": "not_event"
      }
    ],
    [
      {
        "show_label": "691a29b4-242a-4b78-8a27-b132bf43727a",
        "event_name": "app_launch",
        "event_id": 246200677,
        "event_type": "origin",
        "logic": true,
        "event_indicator": "events",
        "sequence_first": true,
        "next_query_label": "7543fcc4-77fa-4fa8-be04-0403a0993ed2",
        "condition": {
          "period": {
            "granularity": "day",
            "type": "past_range",
            "spans": [
              {
                "type": "past",
                "past": {
                  "amount": 7,
                  "unit": "day"
                }
              },
              {
                "type": "past",
                "past": {
                  "amount": 1,
                  "unit": "day"
                }
              }
            ],
            "timezone": "Asia/Shanghai",
            "week_start": 1
          },
          "property_operation": ">",
          "property_values": [
            0
          ]
        },
        "filters": [
          {
            "expression": {
              "logic": "and",
              "conditions": [
                {
                  "property_type": "common_param",
                  "property_name": "os_name",
                  "property_compose_type": "origin",
                  "property_operation": "=",
                  "property_values": [
                    "ios"
                  ]
                }
              ]
            }
          }
        ],
        "cohort_condition_type": "events"
      },
      {
        "show_label": "7543fcc4-77fa-4fa8-be04-0403a0993ed2",
        "event_name": "goods_order_pay",
        "event_id": 246222252,
        "event_type": "origin",
        "logic": true,
        "event_indicator": "events",
        "sequence_first": false,
        "next_query_label": null,
        "condition": {
          "period": {
            "granularity": "day",
            "type": "past_range",
            "spans": [
              {
                "type": "past",
                "past": {
                  "amount": 7,
                  "unit": "day"
                }
              },
              {
                "type": "past",
                "past": {
                  "amount": 1,
                  "unit": "day"
                }
              }
            ],
            "timezone": "Asia/Shanghai",
            "week_start": 1
          },
          "property_operation": ">",
          "property_values": [
            0
          ]
        },
        "filters": [
          {
            "expression": {
              "logic": "and",
              "conditions": [
                {
                  "property_type": "common_param",
                  "property_name": "app_channel",
                  "property_compose_type": "origin",
                  "property_operation": "=",
                  "property_values": [
                    "抖音视频"
                  ]
                }
              ]
            }
          }
        ],
        "cohort_condition_type": "events"
      }
    ]
  ]
}
```

# 2. 圈选DSL设计

- 规则表达式：RuleExpression 结构
  - 一个规则表达式包含多个规则组
- 规则组：RuleGroup 结构
  - 一个规则组包含多个规则
- 规则 Rule
  - 支持4种规则(type)：1-标签规则、2-群组规则、3-事件规则、4-行为序列规则
  - 标签规则和群组规则：只有过滤条件表达式 RuleFilterExpression
    - 过滤条件表达式只支持1-标签/2-群组/3-事件属性
    - 过滤条件表达式通过 RuleFilterExpression、RuleFilterGroup、RuleFilter 三级构成
    - RuleFilter 过滤条件包含属性(标签和群组信息)、操作符、操作值
  - 事件规则需要使用过滤条件表达式 RuleFilterExpression 以及独有的 RuleEvent
    - 事件规则包含事件(Event)、指标(RuleMeasure)、时间周期(RuleTimePeriod)三部分
  - 行为序列规则只需要 List<RuleSequence>
    - 行为序列包含多个事件 RuleEvent

示例：
```json
{
  "logic": "OR",
  "rule_groups": [
    {
      "logic": "AND",
      "rules": [
        {
          "type": "1",
          "filter_expression": {
            "logic": "AND",
            "filter_groups": [
              {
                "filters": [
                  {
                    "type": 1,
                    "id": "L1",
                    "name": "性别",
                    "op": "\u003d",
                    "values": [
                      "女"
                    ]
                  }
                ]
              }
            ]
          }
        },
        {
          "type": "2",
          "filter_expression": {
            "logic": "AND",
            "filter_groups": [
              {
                "filters": [
                  {
                    "type": 2,
                    "id": "G1",
                    "name": "VIP用户群组",
                    "op": "\u003d",
                    "values": [
                      "是"
                    ]
                  }
                ]
              }
            ]
          }
        },
        {
          "type": "3",
          "filter_expression": {
            "logic": "AND",
            "filter_groups": [
              {
                "filters": [
                  {
                    "type": 3,
                    "id": "A1",
                    "name": "操作系统",
                    "op": "\u003d",
                    "values": [
                      "iOS"
                    ]
                  }
                ]
              }
            ]
          },
          "event": {
            "event": {
              "eventId": "E121212121",
              "eventName": "用户启动"
            },
            "measure": {
              "name": "总次数",
              "type": "count",
              "op": "\u003e\u003d",
              "values": [
                "1"
              ]
            },
            "period": {
              "type": 2,
              "beginTimestamp": 1774022400000,
              "endTimestamp": 1774022400000,
              "unit": "day",
              "amount": 2
            }
          }
        }
      ]
    },
    {
      "rules": [
        {
          "type": "1",
          "filter_expression": {
            "logic": "AND",
            "filter_groups": [
              {
                "filters": [
                  {
                    "type": 1,
                    "id": "L1",
                    "name": "性别",
                    "op": "\u003d",
                    "values": [
                      "男"
                    ]
                  }
                ]
              }
            ]
          }
        },
        {
          "type": "2",
          "filter_expression": {
            "logic": "AND",
            "filter_groups": [
              {
                "filters": [
                  {
                    "type": 2,
                    "id": "G1",
                    "name": "VIP用户群组",
                    "op": "\u003d",
                    "values": [
                      "是"
                    ]
                  }
                ]
              }
            ]
          }
        },
        {
          "type": "3",
          "filter_expression": {
            "logic": "AND",
            "filter_groups": [
              {
                "filters": [
                  {
                    "type": 3,
                    "id": "A1",
                    "name": "操作系统",
                    "op": "\u003d",
                    "values": [
                      "Android"
                    ]
                  }
                ]
              }
            ]
          },
          "event": {
            "event": {
              "eventId": "E121212121",
              "eventName": "用户启动"
            },
            "measure": {
              "name": "总次数",
              "type": "count",
              "op": "\u003e\u003d",
              "values": [
                "2"
              ]
            },
            "period": {
              "type": 2,
              "beginTimestamp": 1774022400000,
              "endTimestamp": 1774022400000,
              "unit": "day",
              "amount": 2
            }
          }
        }
      ]
    },
    {
      "rules": [
        {
          "type": "4",
          "events": [
            {
              "event": {
                "event": {
                  "eventId": "E1212121232",
                  "eventName": "应用启动"
                },
                "period": {
                  "type": 2,
                  "beginTimestamp": 1774022400000,
                  "endTimestamp": 1774022400000,
                  "unit": "day",
                  "amount": 2
                }
              },
              "filter_expression": {
                "logic": "AND",
                "filter_groups": [
                  {
                    "filters": [
                      {
                        "type": 3,
                        "id": "A1",
                        "name": "操作系统",
                        "op": "\u003d",
                        "values": [
                          "Android"
                        ]
                      }
                    ]
                  }
                ]
              }
            },
            {
              "event": {
                "event": {
                  "eventId": "E1212121232",
                  "eventName": "应用启动"
                },
                "period": {
                  "type": 2,
                  "beginTimestamp": 1774022400000,
                  "endTimestamp": 1774022400000,
                  "unit": "day",
                  "amount": 2
                }
              },
              "filter_expression": {
                "logic": "AND",
                "filter_groups": [
                  {
                    "filters": [
                      {
                        "type": 3,
                        "id": "A1",
                        "name": "操作系统",
                        "op": "\u003d",
                        "values": [
                          "iOS"
                        ]
                      }
                    ]
                  }
                ]
              }
            }
          ]
        }
      ]
    }
  ]
}
```



###




```
{
      "app_id": 2111833,
      "cohort_name": "啊啊",
      "description": "a",
      "cohort_type": 4,
      "refresh_rule": 1,
      "creator": "2000003907",
      "modify_user": "2000003907",
      "cohort_id": 100053765,
      "is_current": true,
      "dsl_content": {
        "periods": [

        ],
        "version": 3,
        "use_app_cloud_id": true,
        "show_option": {
          "__version": "2.0.0",
          "uuid": "01740916-bccd-42a2-81fa-2a9277e0ebf9",
          "name": "标签值1",
          "type": "cohort",
          "period": {
            "granularity": "day",
            "weekStart": 1,
            "beginTime": {
              "timestamp": 1741104000,
              "amount": 7,
              "unit": "day",
              "hour": 0,
              "tab": 2
            },
            "endTime": {
              "timestamp": 1741622400,
              "amount": 2,
              "unit": "day",
              "hour": 23,
              "tab": 3
            },
            "shortcut": "past_7_day"
          },
          "conditions": {
            "logic": "or",
            "conditions": [
              {
                "uuid": "6dd84977-c3ee-4849-b32d-9cf7397a20d4",
                "logic": "and",
                "conditions": [
                  {
                    "uuid": "676c0fc8-6aab-42ed-af78-3de14014205f",
                    "type": "profile",
                    "event": {
                      "event": {
                        "event_type": "origin",
                        "event_name": "any_event",
                        "show_name": "任意事件"
                      },
                      "filters": {
                        "logic": "and",
                        "conditions": [

                        ]
                      },
                      "measure": {
                        "indicator": {
                          "indicator_type": "events"
                        },
                        "label": "总次数"
                      },
                      "operation": {
                        "label": "≥",
                        "value": ">="
                      },
                      "operationValues": [
                        {
                          "uuid": "243094ea-6dc5-4b1c-987b-0cce27885bf8",
                          "label": "1",
                          "value": 1
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1741104000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1741622400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    },
                    "profile": {
                      "filter": {
                        "property_type": "cohort",
                        "property_compose_type": "origin",
                        "name": "cohort",
                        "show_name": "用户分群"
                      },
                      "operation": {
                        "label": "=",
                        "value": "="
                      },
                      "operationValues": [
                        {
                          "value": 100025248,
                          "label": "【2024】通用培训"
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1741104000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1741622400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    },
                    "events": {

                    }
                  },
                  {
                    "uuid": "658c1e9a-aa70-4468-a1bd-16c6070c7904",
                    "type": "event",
                    "event": {
                      "event": {
                        "event_type": "origin",
                        "event_name": "app_launch",
                        "show_name": "应用启动",
                        "event_id": 246200677,
                        "preset": true,
                        "support_indicators": [
                          "events",
                          "count_by_date",
                          "event_days",
                          "consecutive_date",
                          "sum",
                          "avg",
                          "min",
                          "max",
                          "distinct"
                        ],
                        "metric": {

                        },
                        "sub_app_id": null
                      },
                      "filters": {
                        "logic": "and",
                        "conditions": [
                          {
                            "uuid": "89ebecb8-777a-4e67-b3bf-2893d84966b7",
                            "operation": {
                              "label": "=",
                              "alias": "",
                              "tip": "=",
                              "value": "="
                            },
                            "filter": {
                              "property_compose_type": "origin",
                              "property_type": "common_param",
                              "name": "platform",
                              "show_name": "平台类型",
                              "preset": true,
                              "support_operations": [
                                "is_null",
                                "is_not_null",
                                "=",
                                "!=",
                                "not_equal_not_contain_null",
                                "contain",
                                "not_contain",
                                "not_contain_contain_null",
                                "custom_contain",
                                "match",
                                "not_match"
                              ],
                              "value_type": "string",
                              "has_property_dict": false
                            },
                            "operationValues": [
                              {
                                "label": null,
                                "value": "ios"
                              }
                            ]
                          }
                        ]
                      },
                      "measure": {
                        "indicator": {
                          "indicator_type": "events"
                        }
                      },
                      "operation": {
                        "label": ">=",
                        "value": ">="
                      },
                      "operationValues": [
                        {
                          "uuid": "45aeb083-ea64-4121-96c3-fd181825d6e6",
                          "label": "1",
                          "value": 1
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1741104000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1741622400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    },
                    "profile": {
                      "filter": {
                        "property_compose_type": "origin",
                        "property_type": "user_profile",
                        "name": "gender",
                        "show_name": "性别",
                        "preset": true,
                        "support_operations": [
                          "is_null",
                          "is_not_null",
                          "=",
                          "!=",
                          "not_equal_not_contain_null"
                        ],
                        "value_type": "string",
                        "has_property_dict": false
                      },
                      "operation": {
                        "label": "=",
                        "alias": "",
                        "tip": "=",
                        "value": "="
                      },
                      "operationValues": [
                        {
                          "value": "male",
                          "label": "男"
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1741104000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1741622400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    },
                    "events": {

                    }
                  }
                ]
              },
              {
                "uuid": "0fc79397-7402-4fa4-a90e-98b7b50d168d",
                "logic": "and",
                "conditions": [
                  {
                    "uuid": "67fbc5b4-7323-49ce-abed-5a8b5ef07322",
                    "type": "not_profile",
                    "event": {
                      "event": {
                        "event_type": "origin",
                        "event_name": "app_launch",
                        "show_name": "应用启动",
                        "event_id": 246200677,
                        "preset": true,
                        "support_indicators": [
                          "events",
                          "event_users",
                          "events_per_user",
                          "uv_per_au",
                          "pv_per_au",
                          "sum",
                          "avg",
                          "per_user",
                          "pct",
                          "pct_t_digest",
                          "sum_per_au",
                          "min",
                          "max",
                          "distinct",
                          "distinct_user_attr"
                        ],
                        "metric": {

                        },
                        "sub_app_id": null
                      },
                      "filters": {
                        "logic": "and",
                        "conditions": [
                          {
                            "uuid": "58017f68-a907-4a26-8f0a-817c70d00eae",
                            "operation": {
                              "label": "=",
                              "alias": "",
                              "tip": "=",
                              "value": "="
                            },
                            "filter": {
                              "property_compose_type": "origin",
                              "property_type": "event_param",
                              "name": "$os_version",
                              "show_name": "系统版本",
                              "preset": true,
                              "support_operations": [
                                "is_null",
                                "is_not_null",
                                "=",
                                "!=",
                                "not_equal_not_contain_null",
                                "contain",
                                "not_contain",
                                "not_contain_contain_null",
                                "custom_contain",
                                "match",
                                "not_match"
                              ],
                              "value_type": "string",
                              "has_property_dict": false
                            },
                            "operationValues": [
                              {
                                "label": null,
                                "value": "16.6"
                              }
                            ]
                          }
                        ]
                      },
                      "measure": {
                        "indicator": {
                          "indicator_type": "events"
                        }
                      },
                      "operation": {
                        "label": ">=",
                        "value": ">="
                      },
                      "operationValues": [
                        {
                          "uuid": "c1f978c6-cc05-4283-a755-eec223d60c2f",
                          "label": "1",
                          "value": 1
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1741104000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1741622400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    },
                    "events": {

                    },
                    "profile": {
                      "filter": {
                        "property_compose_type": "origin",
                        "property_type": "user_profile",
                        "name": "user_is_new",
                        "show_name": "是否新用户",
                        "preset": true,
                        "support_operations": [
                          "=",
                          "!="
                        ],
                        "value_type": "int",
                        "has_property_dict": false
                      },
                      "operation": {
                        "label": "=",
                        "alias": "",
                        "tip": "=",
                        "value": "="
                      },
                      "operationValues": [
                        {
                          "label": "新用户",
                          "value": 1
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1773504000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1774022400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    }
                  },
                  {
                    "uuid": "872d65d6-5b61-4d2f-aa13-0bac3ecfefd4",
                    "type": "not_event",
                    "event": {
                      "event": {
                        "event_type": "origin",
                        "event_name": "app_terminate",
                        "show_name": "应用退出",
                        "event_id": 246200678,
                        "preset": true,
                        "support_indicators": [
                          "events",
                          "event_users",
                          "events_per_user",
                          "uv_per_au",
                          "pv_per_au",
                          "sum",
                          "avg",
                          "per_user",
                          "pct",
                          "pct_t_digest",
                          "sum_per_au",
                          "min",
                          "max",
                          "distinct",
                          "distinct_user_attr"
                        ],
                        "metric": {

                        },
                        "sub_app_id": null
                      },
                      "filters": {
                        "logic": "and",
                        "conditions": [
                          {
                            "uuid": "4221a99f-5af0-4b62-9f2c-b0693ff19c25",
                            "operation": {
                              "label": "=",
                              "alias": "",
                              "tip": "=",
                              "value": "="
                            },
                            "filter": {
                              "property_compose_type": "origin",
                              "property_type": "common_param",
                              "name": "os_name",
                              "show_name": "操作系统",
                              "preset": true,
                              "support_operations": [
                                "is_null",
                                "is_not_null",
                                "=",
                                "!=",
                                "not_equal_not_contain_null",
                                "contain",
                                "not_contain",
                                "not_contain_contain_null",
                                "custom_contain",
                                "match",
                                "not_match"
                              ],
                              "value_type": "string",
                              "has_property_dict": false
                            },
                            "operationValues": [
                              {
                                "label": null,
                                "value": "ios"
                              }
                            ]
                          }
                        ]
                      },
                      "measure": {
                        "indicator": {
                          "indicator_type": "events"
                        }
                      },
                      "operation": {
                        "label": ">=",
                        "value": ">="
                      },
                      "operationValues": [
                        {
                          "uuid": "5191663e-18da-4298-8873-3daa36275302",
                          "label": "1",
                          "value": 1
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1741104000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1741622400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    },
                    "events": {

                    }
                  }
                ]
              },
              {
                "uuid": "a8149b49-a078-485b-b371-dc180528884c",
                "logic": "and",
                "conditions": [
                  {
                    "uuid": "6e7312c1-64a0-450c-86d6-ca0c8fcfddb3",
                    "type": "events",
                    "event": {
                      "event": null,
                      "filters": {
                        "logic": "and",
                        "conditions": [

                        ]
                      },
                      "measure": {
                        "indicator": {
                          "indicator_type": "events"
                        },
                        "label": "总次数"
                      },
                      "operation": {
                        "label": "≥",
                        "value": ">="
                      },
                      "operationValues": [
                        {
                          "uuid": "6ef96582-bcb7-40ec-9097-92f3c0b69dd0",
                          "label": "1",
                          "value": 1
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1773504000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1774022400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    },
                    "events": {
                      "events": [
                        {
                          "uuid": "691a29b4-242a-4b78-8a27-b132bf43727a",
                          "event": {
                            "event_type": "origin",
                            "event_name": "app_launch",
                            "show_name": "应用启动",
                            "event_id": 246200677,
                            "preset": true,
                            "support_indicators": [
                              "events",
                              "count_by_date",
                              "event_days",
                              "consecutive_date",
                              "sum",
                              "avg",
                              "min",
                              "max",
                              "distinct"
                            ],
                            "metric": {

                            },
                            "sub_app_id": null
                          },
                          "filters": {
                            "logic": "and",
                            "conditions": [
                              {
                                "uuid": "6d70bb9f-91b8-43c2-9347-7d91fc8115ae",
                                "filter": {
                                  "property_compose_type": "origin",
                                  "property_type": "common_param",
                                  "name": "os_name",
                                  "show_name": "操作系统",
                                  "preset": true,
                                  "support_operations": [
                                    "is_null",
                                    "is_not_null",
                                    "=",
                                    "!=",
                                    "not_equal_not_contain_null",
                                    "contain",
                                    "not_contain",
                                    "not_contain_contain_null",
                                    "custom_contain",
                                    "match",
                                    "not_match"
                                  ],
                                  "value_type": "string",
                                  "has_property_dict": false
                                },
                                "operation": {
                                  "label": "=",
                                  "alias": "",
                                  "tip": "=",
                                  "value": "="
                                },
                                "operationValues": [
                                  {
                                    "label": null,
                                    "value": "ios"
                                  }
                                ]
                              }
                            ]
                          }
                        },
                        {
                          "event": {
                            "event_type": "origin",
                            "event_name": "goods_order_pay",
                            "show_name": "商品订单支付",
                            "event_id": 246222252,
                            "preset": false,
                            "support_indicators": [
                              "events",
                              "count_by_date",
                              "event_days",
                              "consecutive_date",
                              "sum",
                              "avg",
                              "min",
                              "max",
                              "distinct"
                            ],
                            "metric": {

                            },
                            "sub_app_id": null
                          },
                          "filters": {
                            "logic": "and",
                            "conditions": [
                              {
                                "uuid": "5c4f1281-7968-40cc-a62a-1ee51ce308b8",
                                "filter": {
                                  "property_compose_type": "origin",
                                  "property_type": "common_param",
                                  "name": "app_channel",
                                  "show_name": "渠道",
                                  "preset": true,
                                  "support_operations": [
                                    "is_null",
                                    "is_not_null",
                                    "=",
                                    "!=",
                                    "not_equal_not_contain_null",
                                    "contain",
                                    "not_contain",
                                    "not_contain_contain_null",
                                    "custom_contain",
                                    "match",
                                    "not_match"
                                  ],
                                  "value_type": "string",
                                  "has_property_dict": false
                                },
                                "operation": {
                                  "label": "=",
                                  "alias": "",
                                  "tip": "=",
                                  "value": "="
                                },
                                "operationValues": [
                                  {
                                    "label": null,
                                    "value": "抖音视频"
                                  }
                                ]
                              }
                            ]
                          },
                          "uuid": "7543fcc4-77fa-4fa8-be04-0403a0993ed2"
                        }
                      ],
                      "period": {
                        "granularity": "day",
                        "weekStart": 1,
                        "beginTime": {
                          "timestamp": 1773504000,
                          "amount": 7,
                          "unit": "day",
                          "hour": 0,
                          "tab": 2
                        },
                        "endTime": {
                          "timestamp": 1774022400,
                          "amount": 2,
                          "unit": "day",
                          "hour": 23,
                          "tab": 3
                        },
                        "shortcut": "past_7_day"
                      }
                    }
                  }
                ]
              }
            ]
          },
          "extra": {
            "query_trigger": "modify_condition"
          }
        },
        "resources": [
          {
            "project_ids": [
              2111833
            ],
            "subject_ids": [
              5000012
            ],
            "app_ids": [

            ]
          }
        ],
        "app_ids": [

        ],
        "content": {
          "option": {
            "cohort": {
              "outer_logic": "or"
            }
          },
          "query_type": "cohort_v3_idlist",
          "profile_filters": [

          ],
          "profile_groups": [

          ],
          "queries": [
            [
              {
                "show_label": "676c0fc8-6aab-42ed-af78-3de14014205f",
                "event_indicator": "events",
                "logic": true,
                "condition": {
                  "property_operation": ">",
                  "property_values": [
                    0
                  ]
                },
                "filters": [
                  {
                    "expression": {
                      "logic": "and",
                      "conditions": [
                        {
                          "property_type": "cohort",
                          "property_name": "cohort",
                          "property_compose_type": "origin",
                          "property_operation": "=",
                          "property_values": [
                            100025248
                          ]
                        }
                      ]
                    }
                  }
                ],
                "cohort_condition_type": "profile"
              },
              {
                "show_label": "658c1e9a-aa70-4468-a1bd-16c6070c7904",
                "event_name": "app_launch",
                "event_type": "origin",
                "event_id": 246200677,
                "logic": true,
                "event_indicator": "events",
                "measure_info": {

                },
                "condition": {
                  "property_operation": ">=",
                  "property_values": [
                    1
                  ],
                  "period": {
                    "granularity": "day",
                    "type": "past_range",
                    "spans": [
                      {
                        "type": "past",
                        "past": {
                          "amount": 7,
                          "unit": "day"
                        }
                      },
                      {
                        "type": "past",
                        "past": {
                          "amount": 1,
                          "unit": "day"
                        }
                      }
                    ],
                    "timezone": "Asia/Shanghai",
                    "week_start": 1
                  }
                },
                "filters": [
                  {
                    "expression": {
                      "logic": "and",
                      "conditions": [
                        {
                          "property_type": "common_param",
                          "property_name": "platform",
                          "property_compose_type": "origin",
                          "property_operation": "=",
                          "property_values": [
                            "ios"
                          ]
                        }
                      ]
                    }
                  }
                ],
                "cohort_condition_type": "event"
              }
            ],
            [
              {
                "show_label": "67fbc5b4-7323-49ce-abed-5a8b5ef07322",
                "event_indicator": "events",
                "logic": false,
                "condition": {
                  "property_operation": ">",
                  "property_values": [
                    0
                  ]
                },
                "filters": [
                  {
                    "expression": {
                      "logic": "and",
                      "conditions": [
                        {
                          "property_type": "user_profile",
                          "property_name": "user_is_new",
                          "property_compose_type": "origin",
                          "property_operation": "=",
                          "property_values": [
                            1
                          ]
                        }
                      ]
                    }
                  }
                ],
                "cohort_condition_type": "not_profile"
              },
              {
                "show_label": "872d65d6-5b61-4d2f-aa13-0bac3ecfefd4",
                "event_name": "app_terminate",
                "event_type": "origin",
                "event_id": 246200678,
                "logic": false,
                "event_indicator": "events",
                "measure_info": {

                },
                "condition": {
                  "property_operation": ">=",
                  "property_values": [
                    1
                  ],
                  "period": {
                    "granularity": "day",
                    "type": "past_range",
                    "spans": [
                      {
                        "type": "past",
                        "past": {
                          "amount": 7,
                          "unit": "day"
                        }
                      },
                      {
                        "type": "past",
                        "past": {
                          "amount": 1,
                          "unit": "day"
                        }
                      }
                    ],
                    "timezone": "Asia/Shanghai",
                    "week_start": 1
                  }
                },
                "filters": [
                  {
                    "expression": {
                      "logic": "and",
                      "conditions": [
                        {
                          "property_type": "common_param",
                          "property_name": "os_name",
                          "property_compose_type": "origin",
                          "property_operation": "=",
                          "property_values": [
                            "ios"
                          ]
                        }
                      ]
                    }
                  }
                ],
                "cohort_condition_type": "not_event"
              }
            ],
            [
              {
                "show_label": "691a29b4-242a-4b78-8a27-b132bf43727a",
                "event_name": "app_launch",
                "event_id": 246200677,
                "event_type": "origin",
                "logic": true,
                "event_indicator": "events",
                "sequence_first": true,
                "next_query_label": "7543fcc4-77fa-4fa8-be04-0403a0993ed2",
                "condition": {
                  "period": {
                    "granularity": "day",
                    "type": "past_range",
                    "spans": [
                      {
                        "type": "past",
                        "past": {
                          "amount": 7,
                          "unit": "day"
                        }
                      },
                      {
                        "type": "past",
                        "past": {
                          "amount": 1,
                          "unit": "day"
                        }
                      }
                    ],
                    "timezone": "Asia/Shanghai",
                    "week_start": 1
                  },
                  "property_operation": ">",
                  "property_values": [
                    0
                  ]
                },
                "filters": [
                  {
                    "expression": {
                      "logic": "and",
                      "conditions": [
                        {
                          "property_type": "common_param",
                          "property_name": "os_name",
                          "property_compose_type": "origin",
                          "property_operation": "=",
                          "property_values": [
                            "ios"
                          ]
                        }
                      ]
                    }
                  }
                ],
                "cohort_condition_type": "events"
              },
              {
                "show_label": "7543fcc4-77fa-4fa8-be04-0403a0993ed2",
                "event_name": "goods_order_pay",
                "event_id": 246222252,
                "event_type": "origin",
                "logic": true,
                "event_indicator": "events",
                "sequence_first": false,
                "next_query_label": null,
                "condition": {
                  "period": {
                    "granularity": "day",
                    "type": "past_range",
                    "spans": [
                      {
                        "type": "past",
                        "past": {
                          "amount": 7,
                          "unit": "day"
                        }
                      },
                      {
                        "type": "past",
                        "past": {
                          "amount": 1,
                          "unit": "day"
                        }
                      }
                    ],
                    "timezone": "Asia/Shanghai",
                    "week_start": 1
                  },
                  "property_operation": ">",
                  "property_values": [
                    0
                  ]
                },
                "filters": [
                  {
                    "expression": {
                      "logic": "and",
                      "conditions": [
                        {
                          "property_type": "common_param",
                          "property_name": "app_channel",
                          "property_compose_type": "origin",
                          "property_operation": "=",
                          "property_values": [
                            "抖音视频"
                          ]
                        }
                      ]
                    }
                  }
                ],
                "cohort_condition_type": "events"
              }
            ]
          ]
        },
        "timezone": "Asia/Shanghai"
      },
      "modify_time": 1774152817,
      "creator_time": 1741778550,
      "daily_refresh_time": {

      },
      "id": 100053765,
      "modify_user_info": {
        "username": "2100084282",
        "nickname": "smartsi",
        "email": "",
        "head_url": "https://sf1-ttcdn-tos.pstatp.com/obj/byterangers-avatar/bEFEk2100042811.png",
        "user_config": {
          "lang": "zh_CN",
          "current_app_id": 20000341,
          "current_project_id": 2111833
        },
        "id": 2000003907,
        "sub_account_id": ""
      }
    }
```






```
{
    "app_id": 2111833,
    "cohort_name": "啊啊",
    "description": "a",
    "cohort_type": 4,
    "refresh_rule": 1,
    "creator": "2000003907",
    "modify_user": "2000003907",
    "id": 48664,
    "cohort_id": 100053765,
    "is_current": false,
    "dsl_content": {
      "periods": [

      ],
      "version": 3,
      "use_app_cloud_id": true,
      "show_option": {
        "__version": "2.0.0",
        "uuid": "01740916-bccd-42a2-81fa-2a9277e0ebf9",
        "name": "标签值1",
        "type": "cohort",
        "period": {
          "granularity": "day",
          "weekStart": 1,
          "beginTime": {
            "timestamp": 1741104000,
            "amount": 7,
            "unit": "day",
            "hour": 0,
            "tab": 2
          },
          "endTime": {
            "timestamp": 1741622400,
            "amount": 2,
            "unit": "day",
            "hour": 23,
            "tab": 3
          },
          "shortcut": "past_7_day"
        },
        "conditions": {
          "logic": "and",
          "conditions": [
            {
              "uuid": "6dd84977-c3ee-4849-b32d-9cf7397a20d4",
              "logic": "or",
              "conditions": [
                {
                  "uuid": "676c0fc8-6aab-42ed-af78-3de14014205f",
                  "type": "profile",
                  "event": {
                    "event": {
                      "event_type": "origin",
                      "event_name": "any_event",
                      "show_name": "任意事件"
                    },
                    "filters": {
                      "logic": "and",
                      "conditions": [

                      ]
                    },
                    "measure": {
                      "indicator": {
                        "indicator_type": "events"
                      },
                      "label": "总次数"
                    },
                    "operation": {
                      "label": "≥",
                      "value": ">="
                    },
                    "operationValues": [
                      {
                        "uuid": "243094ea-6dc5-4b1c-987b-0cce27885bf8",
                        "label": "1",
                        "value": 1
                      }
                    ],
                    "period": {
                      "granularity": "day",
                      "weekStart": 1,
                      "beginTime": {
                        "timestamp": 1741104000,
                        "amount": 7,
                        "unit": "day",
                        "hour": 0,
                        "tab": 2
                      },
                      "endTime": {
                        "timestamp": 1741622400,
                        "amount": 2,
                        "unit": "day",
                        "hour": 23,
                        "tab": 3
                      },
                      "shortcut": "past_7_day"
                    }
                  },
                  "profile": {
                    "filter": {
                      "property_type": "cohort",
                      "property_compose_type": "origin",
                      "name": "cohort",
                      "show_name": "用户分群"
                    },
                    "operation": {
                      "label": "=",
                      "value": "="
                    },
                    "operationValues": [
                      {
                        "value": 100025248,
                        "label": "【2024】通用培训"
                      }
                    ],
                    "period": {
                      "granularity": "day",
                      "weekStart": 1,
                      "beginTime": {
                        "timestamp": 1741104000,
                        "amount": 7,
                        "unit": "day",
                        "hour": 0,
                        "tab": 2
                      },
                      "endTime": {
                        "timestamp": 1741622400,
                        "amount": 2,
                        "unit": "day",
                        "hour": 23,
                        "tab": 3
                      },
                      "shortcut": "past_7_day"
                    }
                  },
                  "events": {

                  }
                },
                {
                  "uuid": "658c1e9a-aa70-4468-a1bd-16c6070c7904",
                  "type": "not_profile",
                  "event": {
                    "event": {
                      "event_type": "origin",
                      "event_name": "any_event",
                      "show_name": "任意事件"
                    },
                    "filters": {
                      "logic": "and",
                      "conditions": [

                      ]
                    },
                    "measure": {
                      "indicator": {
                        "indicator_type": "events"
                      },
                      "label": "总次数"
                    },
                    "operation": {
                      "label": "≥",
                      "value": ">="
                    },
                    "operationValues": [
                      {
                        "uuid": "bbfe9935-8dd5-41ad-935d-3b048022bd26",
                        "label": "1",
                        "value": 1
                      }
                    ],
                    "period": {
                      "granularity": "day",
                      "weekStart": 1,
                      "beginTime": {
                        "timestamp": 1741104000,
                        "amount": 7,
                        "unit": "day",
                        "hour": 0,
                        "tab": 2
                      },
                      "endTime": {
                        "timestamp": 1741622400,
                        "amount": 2,
                        "unit": "day",
                        "hour": 23,
                        "tab": 3
                      },
                      "shortcut": "past_7_day"
                    }
                  },
                  "profile": {
                    "filter": {
                      "property_compose_type": "origin",
                      "property_type": "user_profile",
                      "name": "gender",
                      "show_name": "性别",
                      "preset": true,
                      "support_operations": [
                        "is_null",
                        "is_not_null",
                        "=",
                        "!=",
                        "not_equal_not_contain_null"
                      ],
                      "value_type": "string",
                      "has_property_dict": false
                    },
                    "operation": {
                      "label": "=",
                      "alias": "",
                      "tip": "=",
                      "value": "="
                    },
                    "operationValues": [
                      {
                        "value": "male",
                        "label": "男"
                      }
                    ],
                    "period": {
                      "granularity": "day",
                      "weekStart": 1,
                      "beginTime": {
                        "timestamp": 1741104000,
                        "amount": 7,
                        "unit": "day",
                        "hour": 0,
                        "tab": 2
                      },
                      "endTime": {
                        "timestamp": 1741622400,
                        "amount": 2,
                        "unit": "day",
                        "hour": 23,
                        "tab": 3
                      },
                      "shortcut": "past_7_day"
                    }
                  },
                  "events": {

                  }
                }
              ]
            },
            {
              "uuid": "0fc79397-7402-4fa4-a90e-98b7b50d168d",
              "logic": "or",
              "conditions": [
                {
                  "uuid": "67fbc5b4-7323-49ce-abed-5a8b5ef07322",
                  "type": "event",
                  "event": {
                    "event": {
                      "event_type": "origin",
                      "event_name": "app_launch",
                      "show_name": "应用启动",
                      "event_id": 246200677,
                      "preset": true,
                      "support_indicators": [
                        "events",
                        "event_users",
                        "events_per_user",
                        "uv_per_au",
                        "pv_per_au",
                        "sum",
                        "avg",
                        "per_user",
                        "pct",
                        "pct_t_digest",
                        "sum_per_au",
                        "min",
                        "max",
                        "distinct",
                        "distinct_user_attr"
                      ],
                      "metric": {

                      },
                      "sub_app_id": null
                    },
                    "filters": {
                      "logic": "and",
                      "conditions": [

                      ]
                    },
                    "measure": {
                      "indicator": {
                        "indicator_type": "events"
                      }
                    },
                    "operation": {
                      "label": ">=",
                      "value": ">="
                    },
                    "operationValues": [
                      {
                        "uuid": "c1f978c6-cc05-4283-a755-eec223d60c2f",
                        "label": "1",
                        "value": 1
                      }
                    ],
                    "period": {
                      "granularity": "day",
                      "weekStart": 1,
                      "beginTime": {
                        "timestamp": 1741104000,
                        "amount": 7,
                        "unit": "day",
                        "hour": 0,
                        "tab": 2
                      },
                      "endTime": {
                        "timestamp": 1741622400,
                        "amount": 2,
                        "unit": "day",
                        "hour": 23,
                        "tab": 3
                      },
                      "shortcut": "past_7_day"
                    }
                  },
                  "events": {

                  }
                },
                {
                  "uuid": "872d65d6-5b61-4d2f-aa13-0bac3ecfefd4",
                  "type": "not_event",
                  "event": {
                    "event": {
                      "event_type": "origin",
                      "event_name": "app_terminate",
                      "show_name": "应用退出",
                      "event_id": 246200678,
                      "preset": true,
                      "support_indicators": [
                        "events",
                        "event_users",
                        "events_per_user",
                        "uv_per_au",
                        "pv_per_au",
                        "sum",
                        "avg",
                        "per_user",
                        "pct",
                        "pct_t_digest",
                        "sum_per_au",
                        "min",
                        "max",
                        "distinct",
                        "distinct_user_attr"
                      ],
                      "metric": {

                      },
                      "sub_app_id": null
                    },
                    "filters": {
                      "logic": "and",
                      "conditions": [

                      ]
                    },
                    "measure": {
                      "indicator": {
                        "indicator_type": "events"
                      }
                    },
                    "operation": {
                      "label": ">=",
                      "value": ">="
                    },
                    "operationValues": [
                      {
                        "uuid": "5191663e-18da-4298-8873-3daa36275302",
                        "label": "1",
                        "value": 1
                      }
                    ],
                    "period": {
                      "granularity": "day",
                      "weekStart": 1,
                      "beginTime": {
                        "timestamp": 1741104000,
                        "amount": 7,
                        "unit": "day",
                        "hour": 0,
                        "tab": 2
                      },
                      "endTime": {
                        "timestamp": 1741622400,
                        "amount": 2,
                        "unit": "day",
                        "hour": 23,
                        "tab": 3
                      },
                      "shortcut": "past_7_day"
                    }
                  },
                  "events": {

                  }
                }
              ]
            }
          ]
        }
      },
      "resources": [
        {
          "project_ids": [
            2111833
          ],
          "subject_ids": [
            5000012
          ],
          "app_ids": [

          ]
        }
      ],
      "app_ids": [

      ],
      "content": {
        "option": {
          "cohort": {
            "outer_logic": "and"
          }
        },
        "query_type": "cohort_v3_idlist",
        "profile_filters": [

        ],
        "profile_groups": [

        ],
        "queries": [
          [
            {
              "show_label": "676c0fc8-6aab-42ed-af78-3de14014205f",
              "event_indicator": "events",
              "logic": true,
              "condition": {
                "property_operation": ">",
                "property_values": [
                  0
                ]
              },
              "filters": [
                {
                  "expression": {
                    "logic": "and",
                    "conditions": [
                      {
                        "property_type": "cohort",
                        "property_name": "cohort",
                        "property_compose_type": "origin",
                        "property_operation": "=",
                        "property_values": [
                          100025248
                        ]
                      }
                    ]
                  }
                }
              ],
              "cohort_condition_type": "profile"
            },
            {
              "show_label": "658c1e9a-aa70-4468-a1bd-16c6070c7904",
              "event_indicator": "events",
              "logic": false,
              "condition": {
                "property_operation": ">",
                "property_values": [
                  0
                ]
              },
              "filters": [
                {
                  "expression": {
                    "logic": "and",
                    "conditions": [
                      {
                        "property_type": "user_profile",
                        "property_name": "gender",
                        "property_compose_type": "origin",
                        "property_operation": "=",
                        "property_values": [
                          "male"
                        ]
                      }
                    ]
                  }
                }
              ],
              "cohort_condition_type": "not_profile"
            }
          ],
          [
            {
              "show_label": "67fbc5b4-7323-49ce-abed-5a8b5ef07322",
              "event_name": "app_launch",
              "event_type": "origin",
              "event_id": 246200677,
              "logic": true,
              "event_indicator": "events",
              "measure_info": {

              },
              "condition": {
                "property_operation": ">=",
                "property_values": [
                  1
                ],
                "period": {
                  "granularity": "day",
                  "type": "past_range",
                  "spans": [
                    {
                      "type": "past",
                      "past": {
                        "amount": 7,
                        "unit": "day"
                      }
                    },
                    {
                      "type": "past",
                      "past": {
                        "amount": 1,
                        "unit": "day"
                      }
                    }
                  ],
                  "timezone": "Asia/Shanghai",
                  "week_start": 1
                }
              },
              "filters": [
                {
                  "expression": {
                    "logic": "and",
                    "conditions": [

                    ]
                  }
                }
              ],
              "cohort_condition_type": "event"
            },
            {
              "show_label": "872d65d6-5b61-4d2f-aa13-0bac3ecfefd4",
              "event_name": "app_terminate",
              "event_type": "origin",
              "event_id": 246200678,
              "logic": false,
              "event_indicator": "events",
              "measure_info": {

              },
              "condition": {
                "property_operation": ">=",
                "property_values": [
                  1
                ],
                "period": {
                  "granularity": "day",
                  "type": "past_range",
                  "spans": [
                    {
                      "type": "past",
                      "past": {
                        "amount": 7,
                        "unit": "day"
                      }
                    },
                    {
                      "type": "past",
                      "past": {
                        "amount": 1,
                        "unit": "day"
                      }
                    }
                  ],
                  "timezone": "Asia/Shanghai",
                  "week_start": 1
                }
              },
              "filters": [
                {
                  "expression": {
                    "logic": "and",
                    "conditions": [

                    ]
                  }
                }
              ],
              "cohort_condition_type": "not_event"
            }
          ]
        ]
      },
      "timezone": "Asia/Shanghai"
    },
    "modify_time": 1774130424,
    "creator_time": 1741778550,
    "modify_user_info": {
      "username": "2100084282",
      "nickname": "smartsi",
      "email": "",
      "head_url": "https://sf1-ttcdn-tos.pstatp.com/obj/byterangers-avatar/bEFEk2100042811.png",
      "user_config": {
        "lang": "zh_CN",
        "current_app_id": 20000341,
        "current_project_id": 2111833
      },
      "id": 2000003907,
      "sub_account_id": ""
    }
  }
```
