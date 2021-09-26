
### 1. 安装Package Control插件

安装插件之前，我们需要首先安装`Package Control`插件, 以后我们安装和管理插件都需要这个插件的帮助。

最简单的安装方法是通过`Sublime Text`控制台。控制台通过`ctrl +`快捷键或者`View> Show Console`菜单进行访问。打开后，将适用于你的`Sublime Text`版本的Python代码粘贴到控制台中。

==Sublime Text 2==
```
import urllib2,os,hashlib; h = 'df21e130d211cfc94d9b0905775a7c0f' + '1e3d39e33b79698005270310898eea76'; pf = 'Package Control.sublime-package'; ipp = sublime.installed_packages_path(); os.makedirs( ipp ) if not os.path.exists(ipp) else None; urllib2.install_opener( urllib2.build_opener( urllib2.ProxyHandler()) ); by = urllib2.urlopen( 'http://packagecontrol.io/' + pf.replace(' ', '%20')).read(); dh = hashlib.sha256(by).hexdigest(); open( os.path.join( ipp, pf), 'wb' ).write(by) if dh == h else None; print('Error validating download (got %s instead of %s), please try manual install' % (dh, h) if dh != h else 'Please restart Sublime Text to finish installation')
```

==Sublime Text 3==

```
import urllib.request,os,hashlib; h = 'df21e130d211cfc94d9b0905775a7c0f' + '1e3d39e33b79698005270310898eea76'; pf = 'Package Control.sublime-package'; ipp = sublime.installed_packages_path(); urllib.request.install_opener( urllib.request.build_opener( urllib.request.ProxyHandler()) ); by = urllib.request.urlopen( 'http://packagecontrol.io/' + pf.replace(' ', '%20')).read(); dh = hashlib.sha256(by).hexdigest(); print('Error validating download (got %s instead of %s), please try manual install' % (dh, h)) if dh != h else open(os.path.join( ipp, pf), 'wb' ).write(by)
```
如果上述代码失效，请去官网查阅对应版本的代码:https://packagecontrol.io/installation#st3．安装完毕重启Sublime Text，就可以使用`Package Control`管理我们的插件。


此代码为你创建已安装的软件包文件夹（如有必要），然后将`Package Control.sublime`软件包下载到其中。 由于Python标准库限制，下载将通过HTTP而不是HTTPS完成，但是该文件将使用SHA-256进行验证。

### 2. 安装MarkdownEditing插件

使用 `Ctrl + Shift + P` 调出面板，然后输入 pci ，选中`Package Control: Install Package`并回车，然后通过输入插件的名字找到插件并回车安装即可。

看到列表的更新之后输入`markdown ed`关键字，选择`MarkdownEditing`回车。 插件安装完毕后需要重新启动Sublime插件才能生效。

下面是我使用sublime编辑代码片断的显示效果:
```java
public Hello{
    public void hello(){
        System.out.println("Hello World");
    }   
}
```

```c
int main(){
    printf("Hello World");
}
```