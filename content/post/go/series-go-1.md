---
title: "Go, how to play?"
date: 2022-02-15T16:01:23+08:00
lastmod: 2022-02-15T16:01:23+08:00
draft: false
tags: ["develop", "go"]
categories: ["develop", "go"]
author: "yesplease"
---
# Go 的IO

## 首要问题，内核中的缓冲和进程中的缓冲

- 内核中的缓冲

  无论进程是否提供缓冲，内核都是提供缓冲的，系统对磁盘的读写都会提供一个缓冲（page/buffer cache），将数据写入到页/块缓冲进行排队，当页/块缓冲达到一定的量时，才能把数据写入磁盘。

- 进程中的缓冲

  是指对输入输出流进行了改进，提供了流缓冲。当调用一个函数向磁盘写数据时，先把数据写入缓冲区，当达到某个条件后，如流缓冲满了，或者刷新流缓冲，这时候才会把数据一次送往内核提供的页/块缓冲区中，再经页/块化重写入磁盘。

  

## Operating System --- linux的文件I/O系统

- 引言

1. 操作系统首先是一个系统，一般由不同的模块组成，往往主要功能是xxx的**增删改查**功能。操作系统主要是管理硬件和提供给我们一个舒适的开发环境的作用。

2. 操作系统可以分为多个**子系统**（VFS算一个），各个子系统又有多个**模块**。

3. 为什么处理器设有两种模式？

   内核态和用户态，**安全第一**。

4. 虚拟内存。其实本质上很简单，就是操作系统将程序常用的数据放到内存里加速访问，不常用的数据放在磁盘上。  这一切对用户程序来说完全是透明的，用户程序可以假装所有数据都在内存里，然后通过虚拟内存地址去访问数据。在这背后，操作系统会自动将数据在主存和磁盘之间进行交换。 

5. [操作系统对内存的管理机](https://www.jianshu.com/p/1ffde2de153f)

   突然想到一个哲学问题，跟生活是相关的。像我们平时生活一样，总是尽可能的把每个东西用尽 用好 用到它的最大极限。同理， Go 语言的内存管理是参考 tcmalloc 实现的，它其实就是利用好了 OS 管理内存的这些特点，来最大化内存分配性能的。 

6. [Go 语言是如何利用底层的这些特性来优化内存的？](https://www.jianshu.com/p/7405b4e11ee2)

   - 内存分配大多时候都是**在用户态**完成的，不需要频繁进入内核态。
   - 每个 P 都有独立的 span cache，多个 CPU 不会并发读写同一块内存，进而减少 CPU L1 cache 的 cacheline 出现 dirty 情况，增大 cpu cache 命中率。
   - 内存碎片的问题，Go 是自己在用户态管理的，在 OS 层面看是没有碎片的，使得操作系统层面对碎片的管理压力也会降低。
   - mcache 的存在使得内存分配不需要加锁。

- Linux中VFS ---> 文件IO系统

![](https://i.loli.net/2021/09/25/XcNevS9PrLdy6IW.png)

​	如上图所示，page cache的本质是由 Linux 内核管理的内存区域。我们通过 mmap 以及 buffered IO 将文件读取到内存空间。实际上，都是读取到 page cache中。

- page cache

  > 除了 Direct IO，与磁盘相关的文件读写都有使用到 page cache技术

  1. kernel 2.6以后（引入了虚拟内存），page cache 面向文件
  2. 文件I/O （系统I/O）操作只和page cache交互
  3. 用在所有**以文件为单元**的场景中，比如网络文件系统
  4. address_space 作为文件系统和页缓存的中间适配器，用来指示一个文件在page cache中已经缓存了的物理页

  - 如何查看OS的 page cache?

    通过读取 /proc/meminfo 文件，能够实时获取系统内存情况：

    ```shell
    $ cat /proc/meminfo
    ...
    Buffers:            1224 kB
    Cached:           111472 kB
    SwapCached:        36364 kB
    Active:          6224232 kB
    Inactive:         979432 kB
    Active(anon):    6173036 kB
    Inactive(anon):   927932 kB
    Active(file):      51196 kB
    Inactive(file):    51500 kB
    ...
    Shmem:             10000 kB
    ...
    SReclaimable:      43532 kB
    ...
    ```

    根据上面的数据，你可以简单得出这样的公式：

    ```
    page cache = buffers + cached + swap = active + inactive + share + swap
    ```

  - 为什么 swap 和 buffers 也是 page cache的一部分？

    因为当匿名页 Inactive(anon)以及 Active(anon) 先被交换到磁盘（out）后，然后再加载回（in）内存中，由于读入到内存后原来地 swap file 还在，所以 swap cached 也可以认为是 File-backed page，即属于 page cache。过程如下图所示：

    ![](https://i.loli.net/2021/09/25/DNl5Ov3rgIc6ZjQ.jpg)

  - page 和 page cache

    page 是内核内存管理分配的基本单位（4KB）

    page cache 由多个page构成（4KB的整数倍）

    **注意**：并不是所有 page 都被组织成为 page cache

    Linux 系统上供用户可访问的内存分为两个类型：

    1. File-backed pages: 文件备份页，也就是page cache中的 page，对应于磁盘上的若干数据块；对于这些页最大的问题是脏页回盘
    2. Anonymous pages: 匿名页不对应磁盘上的任何磁盘数据块，他们是进程的运行内存空间，比如方法栈、局部变量等属性

    两种类型在 swap 机制下的性能比较：

    1. File-backed pages的内存回收代价较低。page cache 通常对应于一个文件上的若干顺序块， 因此可以通过顺序IO的方式落盘。另一方面，如果 page cache 上没有进行写操作（即没有脏页），甚至不会将page cache 回盘，因为数据的内容完全可以通过再次读取磁盘文件得到。

       page cache 的主要难点在于脏页回盘，怎么个难法呢？

    2. Anonymous pages 的内存会后代价较高。因为这种pages 通常随机地写入持久化交换设备。另一方面，无论是否有写操作，为了确保数据不丢失，Anonymous pages在swap时必须持久化到磁盘。

  - swap 与 缺页中断

    [swap 机制](https://lwn.net/Articles/690079/)指地是当物理内存不够用，内存管理单元（MMU）需要提供**调度算法**来回收相关内存空间，然后将清理出来地内存空间给当前内存申请方。

    swap 存在地本质原因是 Linux 系统提供了虚拟内存管理机制。每个进程都认为自己独占内存空间，因此所有进程地内存空间之和远远大于物理内存。所有进程的内存空间之和超过物理内存的部分就需要交换到磁盘上。

    OS以 page 为单位管理内存，当进程发现需要访问的数据不在内存时，OS可能会将数据以页的方式加载到内存中，上述过程被称为缺页中断。当OS发生缺页中断时，就会通过系统调用将 page 再次读到内存中。

    但主内存的空间时有限的，当主内存中不包含可以使用的空间时，OS会选择合适的物理内存逐页驱逐回磁盘，为新的内存页让出位置，选择待驱逐页的过程在OS中叫做页面替换（page replacement）,替换操作又会触发 swap 机制。

    如果物理内存足够大，那么可能不需要 swap 机制，但是 swap 在这种情况下还是有一定优势：对于有发生内存泄漏几率的应用程序（进程）, swap交换分区更是重要，这可以确保内存泄漏不至于导致物理内存不够用，最终导致系统崩溃。但内存泄漏会引起频繁的 swap，此时会非常影响OS的性能。

    Linux 通过一个 swappiness 参数来控制 swap 机制：这个参数可为 0~100，控制系统swap的优先级。

    1. 高数值，较高频率的swap，进程不活跃时将其转换出物理内存
    2. 低数值，较低频率的swap，这可以确保交互式不因为内存空间频繁地交换到磁盘而提高响应延迟。

  - page cache 和 buffer cache

    ```shell
    ~ free -m
                 total       used       free     shared    buffers     cached
    Mem:        128956      96440      32515          0       5368      39900
    -/+ buffers/cache:      51172      77784
    Swap:        16002          0      16001
    ```

    其中，cached 表示当前的页缓存（page cache）占用量，用于缓存文件的页数据；页是逻辑上的概念，因此page cache 是与文件系统同级的

    buffers 表示当前的块缓存（buffer cache）占用量，用于缓存块设备的块数据；块是物理上的概念，因此buffer cache是与块设备驱动程序同级的。

    page cache 和 buffer cache的共同目的都是加速数据IO。写数据时，首先写到缓存，将写入的页标记为 dirty，然后向外部存储 flush，也就是缓存写机制中的 write-back（另一种是 write-through，Linux默认情况下不采用）；读数据时，首先读取缓存，如果命中，再去外部存储读取，并且将读取来的数据页加入缓存。OS**总是积极地**将所有空闲内存都用做 page cache和 buffer cache，当内存不够用时，也会用LRU等算法淘汰缓存页。

    在Linux 2.4 内核之前，page cache 和 buffer cache是完全分离的。但是，块设备大多是磁盘，磁盘上的数据又大多通过文件系统来组织，这种设计导致很多数据被缓存了两次，浪费内存。所以，**在2.4版本之后，两块缓存近似融合在了一起，如果一个文件的页加载到了 page cache，那么同时 buffer cache只需要维护块指向页的指针就可以了。**只有那么没有用文件表示的块，或者绕过了OS直接操作的块（如dd命令），才会真正放到 buffer cache中。因此，我们现在提起 page cache，基本上都同时指 page cache 和 buffer cache 两者。

    下图近似地给出 32位 Linux系统中可能地一种 page cache结构：

    ![](https://i.loli.net/2021/09/25/EQ6xXHyPtrSldbf.png)

    block size = 1KB

    page size = 4KB

    page cache中的每个文件都是一棵**基数树**（radix tree,本质上是多差搜索树），树的每个节点都是一个页。根据文件内的偏移量就可以快速定位到所在的页，如下图所示。

    ![](https://i.loli.net/2021/09/25/U7RhXsNSZfCOj1Y.png)

  - page cache与预读

    OS为基于page cache的读缓存机制提供预读机制（PAGE_READAHEAD）,eg:

    1. 用户线程仅仅请求读取磁盘上文件A的offset为0-3KB范围内的数据，由于磁盘的基本读写单位为 block = 4KB，于是OS至少会读0-4KB的内容，这恰好可以在一个page中装下。
    2. 但是OS处于[局部性原理](https://spongecaptain.cool/SimpleClearFileIO/1.%20page%20cache.html)会选择将磁盘块 offset[4KB,8KB)、[8KB,12KB)、[12KB,16KB)都加载到内存，于是额外在内存中申请了3个page。如下如图所示OS的预读机制：

    ![](https://i.loli.net/2021/09/25/WmBhwcnCUtoNdMQ.gif)

  - page cache与文件持久化的一致性

    现代 Linux 的page cache正如其名，是对磁盘上的 page 的内存缓存，同时可以用于读/写操作。**任何系统引入缓存，就会引发一致性问题**：内存中的数据与磁盘中的数据不一致，如最常见后端架构中的redis缓存与mysql数据库就存在一致性的问题。

    Linux 提供多种机制来保证数据一致性，但无论是单机上的内存与磁盘一致性，还是分布式组件中节点1与节点2、3的数据一致性问题，理解的关键是 trade-off：吞吐量与数据一致性保证是一对矛盾。

    首先，需要我们理解一下文件的数据，文件 = 元数据+数据。

    > 元数据=文件大小+创建时间+访问时间+属主属组等信息

    Linux 采用以下两种方式实现文件一致性：

    1. Write Through(写穿)：向用户层提供特定接口，应用程序可主动调用接口来保证文件一致性；

       以牺牲系统IO吞吐量为代价，向上层应用确保一旦写入，数据就已经落盘，不会丢失。

    2. Write Back(写回)：系统中存在定期任务（表现形式为内核线程），周期性地同步文件系统中文件脏数据块，这就是默认的Linux一致性方案；

       在系统发生宕机的情况下无法确保数据已经落盘，因此存在数据丢失的问题。不过，在程序挂了，如被 kill -9, OS会确保page cache 中的数据落盘。

    两种方法都依赖系统调用，主要分为三种系统调用，可以分别由用户进程与内核进程发起：

    1. fsync(int fd)，将fd 代表的**文件的**脏数据和脏元数据全部刷新到磁盘中
    2. fdatasync(int fd)，将 fd 代表的文件的脏数据刷新至磁盘，同时对必要的（文件大小，而文件修改时间等不属于必要信息）元数据刷新至磁盘中。
    3. sync()，对**系统中所有的**脏的文件数据、元数据都刷新至磁盘中

    描述一下内核线程的相关特性：

    1. 创建的针对**回写任务**的内核线程数由系统中持久存储设备决定，为每个存储设备创建单独的刷新线程；

    2. 关于**多线程的架构**问题，Linux内核采取了 Lighthttp 的做法。即系统中存在一个管理线程和多个刷新线程（每个持久存储设备对应一个刷新线程）。管理线程监控设备上的脏页面情况，若设备一段时间内没有产生脏页面，就销毁设备上的刷新线程；若监测到设备上有脏页面需要回写且尚未为该设备创建刷新线程，那么创建刷新线程处理脏页面回写。而刷新线程的任务较为单调，只负责将设备中的脏页面回写至持久存储设备中。

    3. 刷新线程刷新设备上脏页面大致设计如下：

       每个设备保存脏文件链表，保存的是该设备上存储的脏文件的inode节点。所谓的回写文件脏页面即回写该 inode 链表上的某些文件的脏页面；

       系统中存在多个回写时机。第一，应用程序主动调用回写接口；第二，管理线程周期性地唤醒设备上的回写线程进行回写；第三，某些应用程序/内核任务发现内存不足时要回收部分缓存页面而事先进行脏页面回写，设计一个统一的框架来管理这些回写任务非常有必要。

  - 优势，好处，特点，独特。。。

    1. 加快数据访问

    2. 减少IO次数，提高系统磁盘IO吞吐量

       得益于 page cache的缓存以及预读能力，而程序又往往符合局部性原理。

  - 劣势，缺点，不足。。。
    1. 最直接的缺点就是需要占用**额外**物理内存空间，物理内存在比较紧张的时候可能导致频繁的 swap 操作，最终导致系统的磁盘IO负载上升。（还是那个观点，工业4.0时代，多用点而内存会带来人们的美好生活）
    2. 对应用层**没有提供**很好的管理API，几乎是透明管理。应用层即使想优化 page cache的使用策略也很难进行。因为一些应用选择在用户空间实现自己的 page 管理，而不使用 page cache，例如 mysql 的 innoDB存储引擎以 16KB的页进行管理。（事实是提供了，但某人觉得满足不了他的美好生活，看来人们的美好生活是日益增长的）
    3. 某些场景下[比 Direct IO多一次磁盘IO](https://spongecaptain.cool/SimpleClearFileIO/2.%20DMA%20%E4%B8%8E%E9%9B%B6%E6%8B%B7%E8%B4%9D%E6%8A%80%E6%9C%AF.html)

- 零拷贝

  历史变迁：

  - ​	没有任何优化技术的数据四次拷贝与四次上下文切换

    ![](https://i.loli.net/2021/09/25/pG4a8lrRYcZ5SQs.jpg)

  - DMA参与下的数据四次拷贝

     DMA 也有其局限性，DMA 仅仅能用于设备之间交换数据时进行数据拷贝，但是系统内部的数据拷贝还需要 CPU 进行，例如 CPU 需要负责内核空间数据与用户空间数据之间的拷贝（内存内部的拷贝） 。

    read buffer == page cache

    socket buffer == socket 缓冲区

  ![](https://i.loli.net/2021/09/25/VvQ9Sn67kPTGIx3.jpg)

  - 不同的零拷贝技术适用于不同的应用场景

    - DMA 技术回顾：DMA 负责内存与其他组件之间的数据拷贝，CPU 仅需负责管理，而无需负责全程的数据拷贝；

    - 使用 page cache 的 zero copy：

    - 1. sendfile：一次代替 read/write 系统调用，通过使用 DMA 技术以及传递文件描述符，实现了 zero copy
      2. mmap：仅代替 read 系统调用，将内核空间地址映射为用户空间地址，write 操作直接作用于内核空间。通过 DMA 技术以及地址映射技术，用户空间与内核空间无须数据拷贝，实现了 zero copy

    - 不使用 page cache 的 Direct I/O：读写操作直接在磁盘上进行，不使用 page cache 机制，通常结合用户空间的用户缓存使用。通过 DMA 技术直接与磁盘/网卡进行数据交互，实现了 zero copy

  零拷贝**思想**（ 不是不进行拷贝，而是 CPU 不再全程负责数据拷贝时的搬运工作 ）的一个具体实现。

  一种内存映射文件的方法，实现文件磁盘地址和进程虚拟地址空间中一段虚拟地址的一一映射关系。

   零拷贝的特点是 CPU 不全程负责内存中的数据写入其他组件，CPU 仅仅起到管理的作用 。

  具体实现：

  - **sendfile**（ 用户从磁盘读取一些文件数据后**不需要经过任何计算与处理**就通过网络传输出去 ）

    ![](https://i.loli.net/2021/09/25/HehQIWMnpdSzAZB.jpg)

  - **mmap**，利用 `mmap()` 替换 `read()`，配合 `write()` 调用的整个流程如下： 

    1. 用户进程调用 `mmap()`，从用户态陷入内核态，将内核缓冲区映射到用户缓存区；
    2. DMA 控制器将数据从硬盘拷贝到内核缓冲区（可见其使用了 Page Cache 机制）；
    3. `mmap()` 返回，上下文从内核态切换回用户态；
    4. 用户进程调用 `write()`，尝试把文件数据写到内核里的套接字缓冲区，再次陷入内核态；
    5. CPU 将内核缓冲区中的数据拷贝到的套接字缓冲区；
    6. DMA 控制器将数据从套接字缓冲区拷贝到网卡完成数据传输；
    7. `write()` 返回，上下文从内核态切换回用户态。

  - **splice**

  - **直接 Direct I/O**（自缓存应用程序，数据库管理系统就是这类的一个代表）

    ![](https://i.loli.net/2021/09/25/nailwsNUbyM5xf1.jpg)

   不同的零拷贝技术适用于不同的应用**场景** 。

  - 把mmap单独拿出来说

    用户空间mmap--->内核空间mmap--->缺页异常

    对比，[从内核文件系统看文件读写过程](https://www.cnblogs.com/huxiao-tee/p/4660352.html )

  - 案例

    1. kafaka

       使用 mmap 来对接收到的数据进行持久化，使用 sendfile 从持久化介质中读取数据然后对外发送是一对常用的组合。但是注意，你无法利用 sendfile 来持久化数据，利用 mmap 来实现 CPU 全程不参与数据搬运的数据拷贝。

    2. [mysql 的零拷贝技术]()

  总而言之，常规文件操作需要从磁盘到页缓存再到用户主存的两次数据拷贝。而mmap操控文件，只需要从**磁盘到用户主存**的一次数据拷贝过程。

  说白了，mmap的关键点是实现了用户空间和内核空间的数据直接交互而省去了不同空间数据不通的繁琐过程 。

- mmap 

  一种内存映射文件的方法。将一个文件或者其它对象映射到进程的地址空间，实现文件磁盘地址和进程虚拟地址空间中一段虚拟地址的一一对应关系。实现这样的映射关系后，进程就可以采用指针的方式读写这一段内存，而OS会自动回写脏页面到对应的文件磁盘上，即完成了对文件的操作而不必再调用read、write等系统调用函数。相反，内核空间对这段区域的修改也直接反映到用户空间，从而可以实现不同进程间的文件共享。

  ![](https://i.loli.net/2021/09/25/uhnNDGws3xR24Tk.png)

  - 特点

    1. mmap 向应用程序提供的内存访问接口是内存地址连续的，但是对应的磁盘文件的 block 可以不是地址连续的
    2. mmap 提供的内存空间是虚拟空间，而不是物理空间，因此完全可以分配远远大于物理内存大小的虚拟空间，如16G内存主机可以分配1000G的mmap内存空间
    3. mmap 负责映射文件逻辑上一段连续的数据（物理上可以不连续存储）映射为连续内存，而这里的文件可以是磁盘文件、驱动假造出来的文件以及设备
    4. mmap 由OS负责管理，对同一个文件地址的映射将被所有线程共享，OS确保线程安全及线程可见性

    mmap 的设计很有启发性。基于磁盘的读写单位是 block(4KB)，而基于内存的读写单元是**地址**。换言之，CPU进行一次磁盘读写操作涉及的数据量至少是4KB。但是，进行一次内存操作涉及的数据量是基于地址的，也就是通常的 64bit 。

  - 模型

    ![](https://i.loli.net/2021/09/25/m9QcSfVAJ1dEigv.jpg)

    1. 利用 DMA 技术来取代 CPU 来在内存与其他组件之间的数据拷贝，例如从磁盘到内存，从内存到网卡；
    2. 用户空间的 mmap file 使用虚拟内存，实际上并不占据物理内存，只有在内核空间的 kernel buffer cache 才占据实际的物理内存；
    3. `mmap()` 函数需要配合 `write()` 系统调动进行配合操作，这与 `sendfile()` 函数有所不同，后者一次性代替了 `read()` 以及 `write()`；因此 mmap **也至少**需要 4 次上下文切换；
    4. mmap 仅仅能够避免内核空间到用户空间的全程 CPU 负责的数据拷贝，但是**内核空间内部**还是需要全程 CPU 负责的数据拷贝

  - 流程
    1. 用户进程调用 `mmap()`，从用户态陷入内核态，将内核缓冲区映射到用户缓存区；
    2. DMA 控制器将数据从硬盘拷贝到内核缓冲区（**可见其使用了 Page Cache 机制**）；
    3. `mmap()` 返回，上下文从内核态切换回用户态；
    4. 用户进程调用 `write()`，尝试把文件数据写到内核里的套接字缓冲区，再次陷入内核态；
    5. CPU 将内核缓冲区中的数据拷贝到的套接字缓冲区；
    6. DMA 控制器将数据从套接字缓冲区拷贝到网卡完成数据传输；
    7. `write()` 返回，上下文从内核态切换回用户态。

  - 优势

    1. 简化用户进程编程

       基于缺页异常的懒加载

       数据一致性由OS确保

    2. 读写效率提高：避免内核空间到用户空间的数据拷贝

    3. 避免只读操作时的swap操作

    4. 节约内存

       用户空间与内核空间实际上公用同一份数据

  - 适用场景，非常受限
    1. 多个线程以**只读的方式**同时访问一个文件，这是因为 mmap 机制下多线程共享了同一物理内存空间，因此节约了内存；
    2. mmap 非常适合用于**进程间通信**，这是因为对同一文件对应的 mmap 分配的物理内存天然多线程共享，并可以依赖于操作系统的同步原语；
    3. mmap 虽然比 sendfile 等机制多了一次 CPU 全程参与的内存拷贝，但是用户空间与内核空间并不需要数据拷贝，因此在正确使用情况下并不比 sendfile 效率差；

  - 不适合的场景
    1. 由于 mmap 使用时**必须实现指定好**内存映射的大小，因此 mmap 并不适合变长文件；
    2. 如果**更新频繁**，mmap 避免两态拷贝的优势就被摊还，最终还是落在了大量的脏页回写及由此引发的随机 I/O 上，所以在随机写很多的情况下，mmap 方式在效率上不一定会比带缓冲区的一般写快；
    3. 读/写**小文件**（例如 16K 以下的文件），mmap 与通过 read 系统调用相比有着更高的开销与延迟；同时 mmap 的**刷盘由系统全权控制**，但是在小数据量的情况下由应用本身手动控制更好；
    4. mmap 受限于操作系统内存大小：例如在 32-bits 的操作系统上，虚拟内存总大小也就 2GB，但由于 mmap 必须要在内存中找到一块连续的地址块，此时你就无法对 4GB 大小的文件完全进行 mmap，在这种情况下你必须分多块分别进行 mmap，但是此时地址内存地址已经不再连续，使用 mmap 的意义大打折扣，而且引入了额外的复杂性；

  - 参考

    [认真分析mmap: 是什么 为什么 怎么用](https://www.cnblogs.com/huxiao-tee/p/4660352.html)

    [Linux中 mmap() 函数的内存映射问题理解？](https://www.zhihu.com/question/48161206)

    [When should I use mmap for file access](https://stackoverflow.com/questions/258091/when-should-i-use-mmap-for-file-access)

    [Linux IO原理和Zero-copy技术全面揭秘](https://zhuanlan.zhihu.com/p/308054212)

## Go 的IO

它的 io 和 bufio 是进程中（也可以说是**用户态**）的缓冲。

### Go 和 IO的不解之缘

Go 是一种高性能的编译型语言，天然支持高并发，用户级别封装协程，号称支持百万的协程并发，这个量级不是线程可比的。

- 那Go支持如此高并发的秘诀在于？

  **执行体调度得当**。CPU不停的在不同执行体（goroutine）之间反复横跳。CPU一直在装填和运行不同执行体的指令，G1 不行就搞G2，一刻都不能停，这样才能使得大量的执行体齐头并进，系统才能完成如此高并发的吞吐。

- 那Go适合CPU密集型的程序，还是IO密集型的程序呢？

  **IO密集型。**首先，反推逻辑，CPU密集型就意味着每个执行体都是急需CPU的，G1都吃不饱，切到G2去干嘛，所以CPU密集型的程序最好的情况就是不调度，绑核都来不及呢。想要提高这种程序的性能，就是加钱，买核。

  IO设备和CPU是不同的独立设备。这两者之间的处理可以是并行运行的。Go程序的协程调度可以很好的利用这个关系。让CPU执行程序指令，只负责发送IO，一旦IO被设备接收，CPU不等待完成，就可以处理其他的指令，IO的完成以异步事件的形式触发。这样，IO设备的处理过程和CPU的执行就并行起来了。

- 任何IO都适配Go么？

  Go 语言级别把**网络IO做了异步化**，但是文件IO还是同步的调用

  1. 网络fd可以用epoll池来管理事件，实现异步IO
  2. 文件fd不能用epoll池来管理事件，只能同步IO

  文件想要实现异步IO，当前Linux下有种方式：

  - AIO: 但Go没有封装实现
  - io_uring: 内核版本要求高

### Go的IO长什么样子

- IO接口描述

  `io/io.go`不涉及具体的IO实现，只有**语义接口**

  ```go
  type Reader interface {
   Read(p []byte) (n int, err error)
  }
  
  type Writer interface {
   Write(p []byte) (n int, err error)
  }
  ```

  按照接口的定义维度，大致可以分为3大类：

  - 基础类型

    Reader、Writer、Closer。。。等，描述了最原始的Go的IO的样子。如果你写代码的时候，要实现这些接口，千万要把标准库里的注释读三遍。

  - 组合类型

    往往把最基本的接口组合起来，使用Go的embeding语法糖，比如：ReaderCloser、WriteCloser等

  - 进阶类型

    基于基础接口，加上一些有趣的实现。比如：TeeReader、LimitReader、MultiReader

- IO 通用函数

  io库还有一些基于以上接口的函数，

  - Copy
  - CopyN
  - CopyBuffer

- io/ioutil

  顾名思义，这是一个工具类型的库，util嘛 啥都要有，相当于平时的快捷键。

  这就是个工具库，应付一些简单的场景：

  ReadFile、WriteFile、ReadDir...

### IO 的姿势多种多样

哈哈，这位博主的理解很特别，Go 标准io库定义了基础的语义接口，那具体实现呢？

1. 字节数组可以是 Reader / Writer ？
2. 内存结构体可以是 Reader 吗？
3. 文件可以是 Reader / Writer 吗？
4. 字符串可以是 Reader ？
5. IO 能聚合来提高效率吗？

**都可以**！Go帮我们做好了一切！

io库的拓扑

IO行为都是以io库为中心发散的。

![](https://i.loli.net/2021/09/24/KY9iy2JV7xo5WpP.png)

- io 和 字节的故事： bytes 库

  一句话，内存块可以作为读写的数据流。

  bytes.Reader 可以把[]byte转换成Reader

  bytes.Buffer可以把[]byte转换成Reader、Writer

  ```go
   buffer := make([]byte, 1024)
      readerFromBytes := bytes.NewReader(buffer)
      n, err := io.Copy(ioutil.Discard, readerFromBytes)
      // n == 1024, err == nil
      fmt.Printf("n=%v,err=%v\n",n, err)
  ```

- io和字符串的故事：strings库

  strings.Reader能够把字符串转换成Reader, 这个也特别有意思，直接能把字符串作为读源。

  ```go
      data := "hello world"
      readerFromBytes := strings.NewReader(data)
      n, err := io.Copy(ioutil.Discard, readerFromBytes)
      fmt.Printf("n=%v,err=%v\n",n, err)
  ```

- io和网络的故事：net库

  网络可以作为读写源，抽象成Reader、Writer的形式。

  服务端：

  ```go
  func handleConn(conn net.Conn) {
   defer conn.Close()
   buf := make([]byte, 4096)
   conn.Read(buf)
   conn.Write([]byte("pong: "))
   conn.Write(buf)
  }
   
  func main() {
   server, err := net.Listen("tcp", ":9999")
   if err != nil {
    log.Fatalf("err:%v", err)
   }
   for {
    c, err := server.Accept()
    if err != nil {
     log.Fatalf("err:%v", err)
    }
    go handleConn(c)
   }
  }
  ```

  说明：

  1. net.Listen 创建一个监听套接字，在Go里面封装成了 net.Listener**类型**
  2. Accept 函数返回一个 net.Conn，代表一条网络连接，net.Conn 即是Reader，又是Writer，到了之后各自处理即可

  客户端：

  ```go
  func main() {
      conn, err := net.Dial("tcp", ":9999")
      if err != nil {
          panic(err)
      }
      conn.Write([]byte("hello world\n"))
      io.Copy(os.Stdout, conn)
  }
  ```

  说明：

  1. net.Dail 传入服务器端地址和网络协议类型，即可返回一条和服务端通信的网络连接，返回的结构为 net.Conn
  2. net.Conn既可作为读端，也可为写端

  以上无论是net.Listener，还是net.Conn 都是基于系统调用 socket 之上的一层封装。底层使用的是类似的系统调用：

  - syscall.Socket
  - syscall.Connect
  - syscall.Listen
  - syscall.GetsocketInt

  Go 针对网络fd都会做哪些封装呢？

  1. 创建还是用 socket 调用创建的 fd，创建出来就会立马设置为 nonblock 模式，Go的网络fd天然要使用IO多路复用的方式来走IO
  2. 把 socket fd 丢到 epoll 池里（通过poll.runtime_pollOpen 把 socket 套接字加到epoll池里，底层调用的还是epollctl），监听事件
  3. 封装好读写事件到来的函数回调

- io和文件的故事： os库

  文件IO，这个是我们最常见的IO，文件可以作为读端，也可以作为写端。

  ```
      // 如下，把 test.data 的数据读出来丢到垃圾桶
      fd, err := os.OpenFile("test.data", os.O_RDWR, 0)
      if err != nil {
          panic(err)
      }
      io.Copy(ioutil.Discard, fd)
  ```

  这里返回了一个File类型，不难想象这个是基于文件fd的一层封装。这里面做了什么呢？

  - 调用系统调用 syscall.Open 拿到文件的fd，顺便设置了垃圾回收时候的析构函数

  - stdin、stdout、stderr

    Go把这三个也都抽象成了读写源，这三个类型的变量其实就是File类型的变量，定义在源码 src/os/file.go中

    ```go
    
    var (
     Stdin  = NewFile(uintptr(syscall.Stdin), "/dev/stdin")
     Stdout = NewFile(uintptr(syscall.Stdout), "/dev/stdout")
     Stderr = NewFile(uintptr(syscall.Stderr), "/dev/stderr")
    )
    ```

    标准输入就可以和方便的作为读端（ `Reader` ），标准输出可以作为写端（ `Writer` ）

     eg：**用一行代码实现一个最简单的 echo 回显的程序**

    ```go
    func main() {
        // 一行代码实现回显
        io.Copy(os.Stdout, os.Stdin)
    }
    ```

- 缓存io的故事： bufio库

   **Reader/Writer 可以是缓冲 IO 的数据流** 

  Go缓冲IO是在**底层IO**之上的一层buffer

  形象描述的话，可以说是**用户内存空间的page cache**

   在 c 语言，有人肯定用过 `fopen` 打开的文件（所谓的标准IO）： 

  ``` C
  FILE * fopen ( const char * filename, const char * mode );
  ```

  C 语言的缓冲IO有三种模式：

  - 全缓冲： 只有填满 buffer，才会真正的调用底层IO
  - 行缓冲：不用等填满buffer，遇到换行符，就会把IO下发下去
  - 不缓冲： bypass的模式，每次都是直接掉底层IO

- 四种方式，将数据写入文件

  - os包 f.Write([]byte)

    ```go
    var f *os.File
    var wireteString = "你好,tcy"
    var d1 = []byte(wireteString)
    f, err3 := os.Create("./output.txt") //创建文件
    n2, err3 := f.Write(d1) //写入文件(字节数组)  os方式
    ```

  -  io包的io.WriteString(f, wireteString) 

    ```go
    var wireteString = "你好,tcy"
    n, err1 := io.WriteString(f, wireteString) //写入文件(字符串),io方式,n为几个字节
    f.Sync()  //Sync递交文件的当前内容进行稳定的存储。一般来说，这表示将文件系统的最近写入的数据在内存中的拷贝刷新到硬盘中稳定保存
    ```

  -  ioutil包的ioutil.WriteFile 

    ```go
    var st = []byte(wireteString)
    err2 := ioutil.WriteFile("./output.txt", st, 0666) //写入文件(字节数组),如果文件不存在将按给出的权限创建文件，否则在写入数据之前清空文件。
    
    ```

  -  bufio包中的bufio.NewWriter(f) 

    ```
    var f *os.File
    w := bufio.NewWriter(f) //创建新的 Writer 对象,NewReader创建一个具有默认大小缓冲、从r读取的*Reader
    n4, err3 := w.WriteString("你好,tcy")
    fmt.Printf("写入 %d 个字节n", n4)
    w.Flush() //Flush方法将缓冲中的数据写入下层的io.Writer接口。
    f.Close()
    ```

    

https://zhuanlan.zhihu.com/p/35277219