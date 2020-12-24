

### 1. /etc/profile

对于使用Linux系统的同学而言，肯定非常熟悉主目录下的`.profile`或者`.bash_profile`文件．这些文件用于为shell用户设置环境变量。诸如`umask`以及`PS1`或`PATH`等变量。

`/etc/profile`文件也基本上差不多，但是用于给shell用户设置系统全局环境变量(system wide environmental variables on users shells)。这些变量有时与`.bash_profile`中的变量相同，但是该文件用于为系统中所有shell用户设置初始`PATH`或`PS1`。



~/.profile
```
# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi
```

〜/ .profile：由命令解释器执行，用于登录shell。
如果〜/ .bash_profile或〜/ .bash_login存在，则该文件不会被bash（1）读取。 有关示例，请参阅/ usr / share / doc / bash / examples / startup-files。 文件位于bash-doc包中。

默认的umask在/ etc / profile中设置; 要设置ssh登录的umask，请安装和配置libmam umask包umask 022



#### 1.2 /etc/profile.d

除了设置环境变量之外，`/etc/profile`将在`/etc/profile.d/*.sh`中执行脚本。 如果你计划设置自己的系统环境变量，建议将配置放在`/etc/profile.d`中的shell脚本中。

### 2. /etc/bashrc

像`.bash_profile`一样，通常也会在主目录中看到`.bashrc`文件。 此文件用于设置`bash shell`用户使用的命令别名和函数。

就像`/etc/profile`是`.bash_profile`的系统全局版本一样。Ubuntu系统中`/etc/bash.bashrc`以及Red Hat系统中的`/etc/bashrc`是`.bashrc`的系统全局版本。

有趣的是，在Red Hat实现中，`/etc/bashrc`也会在`/etc/profile.d`中执行shell脚本，但只有当shell用户是交互式Shell（也称为登录Shell）时才可以．

### 3. 什么时候使用

执行这两个文件的区别取决于正在执行的登录用户类型(The difference between when these two files are executed are dependent on the type of login being performed)。 在Linux中，有两种类型的登录shell，即`交互式Shell`和`非交互式Shell`。

- 当用户与`shell`进行交互时(例如，使用命令行模式执行时)，使用交互式Shell． 
- 当用户不与`shell`进行交互时(例如，使用bash脚本执行时)，使用非交互式Shell。


区别很简单，`/etc/profile`只能用于交互式Shell．`/etc/bashrc`既可以用于交互式Shell，也可以用于非交互式Shell。实际上在Ubuntu中，`/etc/profile`直接调用`/etc/bashrc`。

```
# /etc/profile: system-wide .profile file for the Bourne shell (sh(1))
# and Bourne compatible shells (bash(1), ksh(1), ash(1), ...).

if [ "$PS1" ]; then
  if [ "$BASH" ] && [ "$BASH" != "/bin/sh" ]; then
    # The file bash.bashrc already sets the default PS1.
    # PS1='\h:\w\$ '
    if [ -f /etc/bash.bashrc ]; then
      . /etc/bash.bashrc
    fi
  else
    if [ "`id -u`" -eq 0 ]; then
      PS1='# '
    else
      PS1='$ '
    fi
  fi
fi

# The default umask is now handled by pam_umask.
# See pam_umask(8) and /etc/login.defs.

if [ -d /etc/profile.d ]; then
  for i in /etc/profile.d/*.sh; do
    if [ -r $i ]; then
      . $i
    fi
  done
  unset i
fi
```

### 4. 交互式Shell VS 非交互式Shell

为了展示`交互式shell`与`非交互式shell`的区别，我将在我的Ubuntu系统上`/etc/profile`和`/etc/bash.bashrc`中添加一个变量：

```
# /etc/profile
export TESTPROFILE=PROFILE

# /etc/bash.bashrc
export TESTBASHRC=BASHRC
```

#### 4.1 交互式Shell

下面的示例显示了一个交互式Shell，在这种情况下，`/etc/profile`和`/etc/bash.bashrc`都被执行。

```
xiaosi@yoona:~$ su -
root@yoona:~# env | grep TEST
TESTBASHRC=BASHRC
TESTPROFILE=PROFILE
```
#### 4.2 非交互式Shell

在这个例子中，我们通过SSH运行一个非交互的命令; 因为这是一个非交互式Shell，所以只执行`/etc/bash.bashrc`文件:

```
# ssh localhost "env | grep TEST"
root@localhost's password: 
TESTBASHRC=BASHRC
```

### 5. 结论

In my case the applications child processes are not recognizing the umask value set in /etc/profile but do recognize the value in /etc/bashrc. This tells me that the subprocess is starting as a non-interactive shell. While the suggested route of modifying environmental variables is to add a shell script into /etc/profile.d in my case it is better to set the umask value in the /etc/bashrc.





原文：http://bencane.com/2013/09/16/understanding-a-little-more-about-etcprofile-and-etcbashrc/