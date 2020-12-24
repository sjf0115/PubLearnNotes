https://woodding2008.iteye.com/blog/2335200

Spout从0.8.1之后在调用nextTuple方法时，如果没有emit tuple，那么默认需要休眠1ms，这个具体的策略是可配置的，因此可以根据自己的具体场景，进行设置，以达到合理利用cpu资源。
