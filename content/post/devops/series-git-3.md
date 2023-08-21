---
title: "git 常用操作"
date: 2023-07-30T16:01:23+08:00
lastmod: 2023-07-30T16:01:23+08:00
draft: false
tags: ["devops", "git"]
categories: ["devops", "cloudnative"]
author: "yesplease"
---

## git 常用操作


## 一、场景描述

 记录一些常用操作

- git status: 显示工作区和暂存区的状态
- git diff: 显示工作区和暂存区之间的差异
- git diff --cached: 显示暂存区和最新提交之间的差异
- git diff [分支1] [分支2]: 比较两个分支之间的差异
- git grep [关键词]: 在整个代码库中搜索指定关键词
- git stash: 将当前修改暂存起来，切换到其他分支
- git reset --hard [提交号]: 将当前分支的 HEAD 指针指向指定的提交，并重置工作区和暂存区
- git rm [文件]: 从版本控制中移除文件
- git rebase [提交号]: 交互式地合并、重新排序或编辑提交历史的
- git cherry-pick [提交号]: 选择某个提交，并将其应用到当前分支
- git blame [文件]: 显示指定文件的每一行是谁在哪个提交中修改的
- git blame -L [起始行号],[结束行号] [文件]: 仅显示指定行范围的文件是谁修改的
- git revert [提交号]: 创建一个新的提交，用于撤销指定的提交
- git bisect start: 启动二分查找来定位引入问题的提交
- git stash apply: 恢复最近一次暂存的修改，并将其从暂存堆栈中删除
- git reflog: 显示 HEAD 和分支的历史记录，包括已经被删除的提交
- git log --author=[作者]: 显示特定作者的提交历史
- git tag [标签名] [提交号]: 在指定提交上创建一个标签
- git show-branch: 显示本地分支的历史和状态

## 二、问问 gpt[^1]


---
> 解释下git show 

`git show` 是一个非常有用的 Git 命令，它用于显示提交的详细信息和更改的内容。下面是 `git show` 的详细讲解：

基本语法：
```plaintext
git show [提交]
```

参数：
- `[提交]`: 可选参数，表示要查看的提交，默认为最新的提交。

使用 `git show` 命令可以获取以下信息：

1. 提交信息：包括提交哈希值、作者、提交日期和提交消息。

2. 修改的文件：列出了与该提交相关的所有修改过的文件。

3. 文件更改的具体内容：展示了每个文件的具体更改内容，即新增、修改或删除的行。

4. 代码差异：以 diff 的形式显示当前提交与其父提交之间的代码差异。

5. 其他元数据：显示提交中的其他元数据，例如签名和标签。

示例用法：
```plaintext
$ git show
```
这将显示最新提交的详细信息和更改的内容。

```plaintext
$ git show abcdef123456
```
这将显示提交哈希值为 `abcdef123456` 的提交的详细信息和更改的内容。

`git show` 命令在查看历史提交、检查代码更改、审查提交信息等方面非常有用。通过查看提交的详细信息，开发者可以更好地理解代码库的演变历史并进行必要的代码审查和调试。记住，你可以使用其他参数和选项来进一步定制 `git show` 命令的输出。可以通过 `git show --help` 查看详细的帮助文档。

---
>解释下 git rebase -i commit

当你运行 `git rebase -i commit` 命令时，你可以使用交互式界面对提交历史进行编辑。下面是一个示例：

假设你有如下的提交历史：

```
commit C: Add feature C
commit B: Add feature B
commit A: Add feature A
```

现在你想要将提交 B 和提交 C 合并为一个提交，并编辑提交 A 的消息。你可以运行以下命令：

```
git rebase -i commit
```

Git 将会打开交互式界面，其中列出了提交历史的相关信息：

```
pick abcdef1 commit A: Add feature A
pick bcdef23 commit B: Add feature B
pick def4567 commit C: Add feature C
```

你可以对这些操作进行修改，以实现你的目标。在本例中，你可以将提交 B 和提交 C 合并为一个提交，然后编辑提交 A 的消息。你可以修改交互式界面如下：

```
pick abcdef1 commit A: Add feature A
squash bcdef23 commit B: Add feature B
s/commit A: Add feature A/Edit feature A/
```

保存并退出编辑器。Git 将会根据你的指示执行相应的操作。此时，Git 会自动合并提交 B 到提交 A，并修改提交 A 的消息。最终的提交历史将如下所示：

```
commit A: Edit feature A
commit BC: Add feature B and C
```

注意，在上述示例中，使用了 `squash` 命令来将提交 B 合并到提交 A，并使用 `s/commit A: Add feature A/Edit feature A/` 来编辑提交 A 的消息。

请注意，在执行类似于 `git rebase -i` 这样的操作时，一定要小心审查并确认你的更改，以免不小心破坏提交历史。

---
>git bisect 详细介绍下

git bisect 是 Git 提供的一个命令，用于帮助我们通过二分查找定位引入问题的提交。当我们在一个大型项目中发现了一个 bug，并且我们知道在之前的某个提交中出现了这个 bug，但是不知道具体是在哪个提交引入的时候，可以使用 git bisect 命令来快速定位。

下面是 git bisect 的详细使用步骤：

1、首先，进入到你的项目目录中，并确保你在一个干净的状态下（没有未提交的修改）。

2、执行 git bisect start 命令，表示开始二分查找。

3、通过 git bisect bad 命令告诉 Git 当前的代码状态是有问题的（即包含了 bug）。

4、使用 git bisect good [好的提交号] 或者 git bisect good [好的标签名] 命令指定一个已知的“好”（即没有问题的）的提交。

5、Git 会自动切换到一个中间的提交，并要求你测试这个提交是否存在 bug。根据测试结果使用 git bisect bad 或者 git bisect good 命令告诉 Git 这个中间提交是否含有 bug。

6、重复步骤 5，Git 会根据你的测试结果不断地切换到新的中间提交，直到找到引入问题的提交。

7、当 git bisect 定位到引入问题的提交时，Git 会给出相应的提示，并自动返回到该提交。

8、最后，执行 git bisect reset 命令结束二分查找过程，Git 会将你的 HEAD 恢复到初始状态。

通过以上步骤，你可以使用 git bisect 在复杂的代码历史中快速定位 bug 的引入提交。这个命令在大型项目中特别有用，可以节省定位问题的时间和精力。需要注意的是，你需要根据实际情况进行好坏提交的选择，并且在测试过程中保持良好的记录和反馈。

要将之前所有提交中的密码更改为 `***`，可以使用 `git filter-branch` 命令结合自定义脚本来实现。请按照以下步骤进行操作：

1. 首先，在你的项目目录下打开终端，并确保你当前在所需的分支上（例如，`master` 分支）。

2. 运行以下命令来备份你的代码：
   ```plaintext
   git branch backup
   ```

3. 创建一个名为 `replace_password.sh` 的脚本文件，并使用文本编辑器打开它。

4. 在 `replace_password.sh` 文件中，输入以下内容：
   ```plaintext
   #!/bin/bash
   git ls-files -z | while read -d '' -r file; do
     if [[ $file == *"<文件路径>"* ]]; then
       sed -i 's/密码模式/*** /g' "$file"
     fi
   done
   ```
   将 `<文件路径>` 替换为包含密码的文件的路径或文件夹的路径。这将会在指定文件中查找并替换密码。

5. 保存并关闭 `replace_password.sh` 文件。

6. 运行以下命令来添加执行权限给脚本文件：
   ```plaintext
   chmod +x replace_password.sh
   ```

7. 现在，运行以下命令来执行 `git filter-branch` 操作，并使用脚本文件作为过滤器：
   ```plaintext
   git filter-branch --tree-filter '/path/to/replace_password.sh' --prune-empty HEAD
   ```
   将 `/path/to/replace_password.sh` 替换为 `replace_password.sh` 文件的实际路径。

8. Git 将会遍历所有的提交，并在每个提交上运行脚本文件，查找并替换指定文件中的密码。完成后，你的历史提交将被重写。

9. 如果你已经将这些提交推送到远程仓库，你需要使用 `git push --force` 强制推送修改后的提交历史：
   ```plaintext
   git push --force
   ```

这样，你就可以使用自定义脚本来批量替换之前所有提交中的密码。但请注意，执行 `git filter-branch` 操作时，也要小心谨慎，因为它会修改提交历史。确保在操作之前备份代码，并在必要时咨询有经验的 Git 使用者或开发者。

---
>sparse-checkout  详细讲解下

`sparse-checkout` 是 Git 的一个功能，用于部分克隆（partial clone）仓库。它允许你只检出仓库中指定目录或文件的内容，而不是完整地克隆整个仓库。这对于大型仓库或仅需要特定部分代码的情况非常有用，可以显著节省下载和存储空间。

下面是 `sparse-checkout` 的详细讲解：

1. 配置 `sparse-checkout`：在进行部分克隆之前，需先配置 `sparse-checkout`。

   ```shell
   $ git sparse-checkout init
   ```

2. 添加感兴趣的目录或文件：通过指定要检出的目录或文件，告诉 Git 哪些部分是你感兴趣的。

   ```shell
   $ git sparse-checkout set <目录/文件>
   ```

   你可以多次运行该命令来添加多个目录或文件。

3. 完成部分克隆：现在你可以执行部分克隆命令，只拉取感兴趣的部分。

   ```shell
   $ git clone --filter=blob:none <远程仓库URL>
   ```

   注意，在使用 `--filter=blob:none` 标志进行部分克隆时，仓库中的大文件将不会被下载，只有文件元数据（例如文件名和文件大小）会被获取。

4. 更新和同步：一旦你进行了部分克隆，你可以像常规 Git 仓库一样更新和同步。

   ```shell
   $ git pull origin <分支>
   ```

   Git 会根据你配置的 `sparse-checkout` 来更新和同步你感兴趣的部分。

总结来说，`sparse-checkout` 提供了一种灵活的方式来只检出仓库中特定目录或文件的内容。它可以实现部分克隆，节省带宽和存储空间，并提高代码仓库的下载速度。记住，部分克隆功能在 Git 2.25 及更高版本中才可用。

## 三、小结：
附上一些常用缩写：
```sh
alias gc='git config'
alias gs='git status'
alias g='git'
alias ga='git add'
alias gaa='git add -all'
alias gp='git push'
alias gl='git pull'
alias gc='git commit'
alias gcm='git commit -m'
alias gcam='git commit -am'
alias gb='git branch'
alias gbr='git branch -r'
alias gba='git branch -a'
alias gco='git checkout'
alias gcb='git checkout -b'
alias gm='git merge'
alias gd='git diff'
alias gdw='git diff --word-diff'
alias glg='git lg'
```


## 四、参考

[^1]: [gpt]()

[^2]: [git](https://git-scm.com/book/zh/v2)
