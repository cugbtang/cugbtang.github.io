---
title: "git 以前的许多commit中某个文件含有密钥，怎么办？"
date: 2023-07-30T16:01:23+08:00
lastmod: 2023-07-30T16:01:23+08:00
draft: false
tags: ["devops", "git"]
categories: ["devops", "cloudnative"]
author: "yesplease"
---

## git 以前的许多commit中某个文件含有密钥，怎么办？


## 一、场景描述

 在这个项目中，代码的都是在develop分支上进行的， 现在要打tag v1.0.0进行发版。然而，从项目init开始到现在有很多commit，其中某个文件中把密钥直接写在了源码中，最近几次提交才把密钥处理了。



## 二、问问 gpt[^1]

----
> git  一开始项目的很多提交中某个文件含有密钥，最近的几次commit中才把密钥隐藏掉，那么怎样清除之前的很多次commit中密钥; 我想把之前所有提交中密码不为***的都改为***  该怎么操作


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

----

>git filter-branch --tree-filter '/path/to/replace_password.sh' --prune-empty HEAD
  解释下这个命令

当你运行 git filter-branch 命令时，它会遍历 Git 仓库的每个提交，并对每个提交应用指定的过滤器。在这个命令中，我们使用了 --tree-filter 参数来指定一个以树形结构过滤提交的过滤器。

下面解释一下命令中各个部分的含义：

- git filter-branch: 这是执行过滤操作的 Git 命令。

- --tree-filter: 这是指定要应用的过滤器类型。--tree-filter 可以在每个提交的工作目录中运行指定的命令。

- '/path/to/replace_password.sh': 这是具体的过滤器命令。在每个提交中，它运行 /path/to/replace_password.sh 命令来修改

- HEAD: 这是指定要过滤的提交范围。在这个命令中，我们使用 HEAD 表示过滤当前分支上的所有提交。

通过运行上述命令，Git 将会遍历每个提交，并在每个提交上执行指定的命令，移除包含密钥文件的文件。完成后，
## 三、小结：
简化一些：
```sh
 git filter-branch --tree-filter ' sed -i "s/aaa/*** /g" ./initialize/config.go' --prune-empty HEAD

 git push -f
```
 - filter-branch[^2]

## 四、参考

[^1]: [gpt]()

[^2]: [git-filter-branch](https://git-scm.com/book/zh/v2/Git-%E5%B7%A5%E5%85%B7-%E4%BD%BF%E7%94%A8-Git-%E8%B0%83%E8%AF%95)
