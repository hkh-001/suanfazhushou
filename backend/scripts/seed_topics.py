from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import UUID

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.topic import Topic, TopicDependency
from app.models.user import User


TOPICS = [
    {
        "title": "时间复杂度",
        "slug": "time-complexity",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 2,
        "summary": "理解算法运行时间如何随输入规模增长，是判断解法能否通过的基础。",
        "content_markdown": """时间复杂度关注输入规模变大时，算法操作次数的增长趋势。

常见复杂度包括 O(1)、O(log n)、O(n)、O(n log n)、O(n^2)。学习时不只是背结论，而是要能从循环、递归和数据范围判断一个做法是否可行。

刷题时建议先看数据范围，再估算允许的操作数量。例如 n 为 10^5 时，通常 O(n log n) 可以接受，而 O(n^2) 往往不可行。""",
        "estimated_minutes": 30,
        "order_index": 1,
    },
    {
        "title": "数组基础",
        "slug": "array-basics",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 2,
        "summary": "数组用于存储连续的一组数据，是大多数算法题的基础数据结构。",
        "content_markdown": """数组适合按下标快速访问元素。很多题目的核心是正确维护下标、边界和遍历顺序。

学习数组时要特别注意下标从 0 还是 1 开始，循环边界是否包含末尾，以及修改数组时是否影响后续判断。

常见题型包括统计、查找、区间处理、原地更新和简单模拟。""",
        "estimated_minutes": 35,
        "order_index": 2,
    },
    {
        "title": "字符串基础",
        "slug": "string-basics",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 2,
        "summary": "字符串题通常围绕字符遍历、子串、统计和格式处理展开。",
        "content_markdown": """字符串可以看作字符数组，但还包含长度、拼接、切片等语言内置操作。

基础阶段应掌握逐字符遍历、字符计数、大小写处理、判断回文、查找子串等操作。

做字符串题时要注意空串、单字符、空格和换行输入。""",
        "estimated_minutes": 35,
        "order_index": 3,
    },
    {
        "title": "模拟",
        "slug": "simulation",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 3,
        "summary": "模拟题要求把题目规则准确翻译成程序流程。",
        "content_markdown": """模拟题没有固定模板，关键是读懂规则并保持状态更新顺序正确。

建议先列出状态变量，再按题目要求逐步执行。复杂模拟可以拆成多个小函数，减少分支混乱。

常见错误包括漏掉边界情况、状态更新顺序错误、输入输出格式不一致。""",
        "estimated_minutes": 40,
        "order_index": 4,
    },
    {
        "title": "排序",
        "slug": "sorting",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 3,
        "summary": "排序能把数据调整为有序状态，常作为贪心、双指针和二分的前置步骤。",
        "content_markdown": """排序的核心作用是制造顺序，让原本混乱的数据变得容易比较和扫描。

基础阶段需要掌握如何调用语言内置排序、如何自定义排序规则，以及排序后的复杂度通常为 O(n log n)。

很多题目不是考排序算法本身，而是考排序后如何利用顺序。""",
        "estimated_minutes": 35,
        "order_index": 5,
    },
    {
        "title": "前缀和",
        "slug": "prefix-sum",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 4,
        "summary": "前缀和用于快速查询区间和，把多次区间求和从 O(n) 降到 O(1)。",
        "content_markdown": """前缀和数组 `pre[i]` 表示前 i 个元素的总和。区间 `[l, r]` 的和可以通过两个前缀值相减得到。

它适合处理大量静态区间求和问题。学习时要统一下标定义，避免 l 和 r 的边界错误。

常见扩展包括二维前缀和、前缀计数和前缀异或。""",
        "estimated_minutes": 45,
        "order_index": 6,
    },
    {
        "title": "差分",
        "slug": "difference-array",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 4,
        "summary": "差分用于高效处理多次区间修改，最后还原出每个位置的值。",
        "content_markdown": """差分数组记录相邻元素之间的变化。对区间 `[l, r]` 加上一个值，只需要修改两个边界位置。

所有修改完成后，对差分数组做一次前缀和即可得到最终数组。

差分适合区间加、最后统一查询的场景，不适合频繁边修改边查询的场景。""",
        "estimated_minutes": 45,
        "order_index": 7,
    },
    {
        "title": "双指针",
        "slug": "two-pointers",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 5,
        "summary": "双指针通过两个位置协同移动，减少重复枚举。",
        "content_markdown": """双指针常用于有序数组、滑动窗口和区间维护。

关键是明确两个指针分别表示什么，以及每一步移动哪个指针不会漏解。

常见题型包括两数之和变体、去重、最长连续区间和满足条件的窗口。""",
        "estimated_minutes": 50,
        "order_index": 8,
    },
    {
        "title": "二分查找",
        "slug": "binary-search",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 5,
        "summary": "二分查找用于在有序或具有单调性的答案空间中快速定位目标。",
        "content_markdown": """二分的本质是利用单调性，每次排除一半不可能的范围。

学习二分时要重点统一区间写法，例如左闭右闭或左闭右开，并认真处理循环条件和边界更新。

除了数组查找，二分还可以用于二分答案。""",
        "estimated_minutes": 55,
        "order_index": 9,
    },
    {
        "title": "递归基础",
        "slug": "recursion-basics",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 5,
        "summary": "递归把问题拆成更小的同类问题，是 DFS、分治和动态规划的重要基础。",
        "content_markdown": """递归函数通常包含两个部分：递归终止条件，以及把当前问题拆成子问题的递推逻辑。

写递归时要先明确函数含义，再设计边界条件，最后考虑每一层如何向下一层推进。

常见风险包括忘记终止条件、递归层数过深、重复计算过多。""",
        "estimated_minutes": 50,
        "order_index": 10,
    },
    {
        "title": "栈与队列",
        "slug": "stack-queue",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 4,
        "summary": "栈和队列分别对应后进先出和先进先出，是表达顺序关系的基础结构。",
        "content_markdown": """栈适合处理括号匹配、单调栈、递归过程模拟等问题；队列适合处理 BFS 和按顺序扩展的状态。

学习时要理解入栈、出栈、入队、出队的时机，而不是只记 API。

很多图搜索和区间维护技巧都会建立在这两个结构上。""",
        "estimated_minutes": 45,
        "order_index": 11,
    },
    {
        "title": "哈希表",
        "slug": "hash-table",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 4,
        "summary": "哈希表用于快速记录和查询键值关系，常把查找从 O(n) 降到均摊 O(1)。",
        "content_markdown": """哈希表常用于计数、去重、记录位置、判断某个状态是否出现过。

使用哈希表时要明确键的定义，避免把不同状态映射成同一个不完整的键。

在竞赛题中，哈希表经常和前缀和、双指针、图搜索配合使用。""",
        "estimated_minutes": 45,
        "order_index": 12,
    },
    {
        "title": "DFS",
        "slug": "dfs",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 6,
        "summary": "深度优先搜索沿一条路径尽可能深入，适合枚举方案、连通块和回溯。",
        "content_markdown": """DFS 的核心是状态、选择和回退。它常用于树和图的遍历，也用于排列组合等搜索问题。

写 DFS 时要明确当前状态包含哪些信息，哪些状态已经访问过，以及何时返回。

回溯题要特别注意撤销现场，图搜索题要注意 visited 的含义。""",
        "estimated_minutes": 60,
        "order_index": 13,
    },
    {
        "title": "BFS",
        "slug": "bfs",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 6,
        "summary": "广度优先搜索按层扩展，常用于最短步数和状态空间搜索。",
        "content_markdown": """BFS 使用队列维护待扩展状态。由于它按层推进，在边权相同的图中第一次到达某个状态通常就是最短步数。

写 BFS 时要定义好初始状态、转移规则、访问标记和终止条件。

常见题型包括迷宫最短路、单词变换、状态压缩搜索的入门版本。""",
        "estimated_minutes": 60,
        "order_index": 14,
    },
    {
        "title": "贪心",
        "slug": "greedy",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 6,
        "summary": "贪心每一步选择当前看起来最优的方案，需要证明局部最优能导向全局最优。",
        "content_markdown": """贪心不是看到最大或最小就直接选，而是要说明为什么这个选择不会影响最优答案。

常见证明方式包括交换论证、排序后选择、维护不变量。

如果无法证明，建议先尝试构造反例，避免把动态规划题误写成贪心。""",
        "estimated_minutes": 60,
        "order_index": 15,
    },
    {
        "title": "动态规划入门",
        "slug": "dynamic-programming-basics",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 7,
        "summary": "动态规划通过状态和转移复用子问题答案，适合有重叠子问题和最优子结构的问题。",
        "content_markdown": """动态规划的关键步骤是定义状态、写出转移、确定初始化和遍历顺序。

入门阶段建议从一维 DP、二维 DP、路径计数和简单最值问题开始。

不要急着背模板，先解释 `dp[i]` 或 `dp[i][j]` 的含义，再推导它从哪些状态转移而来。""",
        "estimated_minutes": 75,
        "order_index": 16,
    },
    {
        "title": "图基础",
        "slug": "graph-basics",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 6,
        "summary": "图用于描述点和边的关系，是搜索、最短路、拓扑排序等算法的基础。",
        "content_markdown": """图可以用邻接表、邻接矩阵或边集表示。大多数稀疏图题更适合邻接表。

学习图基础时要掌握有向图、无向图、边权、连通性、入度和出度等概念。

图题的第一步通常是把题意转化成点和边。""",
        "estimated_minutes": 60,
        "order_index": 17,
    },
    {
        "title": "树基础",
        "slug": "tree-basics",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 6,
        "summary": "树是一种无环连通图，递归和 DFS 是处理树问题的重要工具。",
        "content_markdown": """树题常围绕父子关系、深度、子树、路径和遍历顺序展开。

基础阶段需要掌握先序、后序、层序遍历，以及如何在 DFS 中维护父节点防止走回头路。

很多树形 DP 和最近公共祖先算法都建立在树基础之上。""",
        "estimated_minutes": 60,
        "order_index": 18,
    },
    {
        "title": "堆与优先队列",
        "slug": "heap-priority-queue",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 6,
        "summary": "堆能快速取出当前最大或最小元素，适合动态维护优先级。",
        "content_markdown": """优先队列常用于 Top K、合并有序序列、Dijkstra 最短路等场景。

使用堆时要明确优先级规则，必要时把多个字段组合成排序键。

堆只能快速访问堆顶，不能高效随机删除任意元素。""",
        "estimated_minutes": 55,
        "order_index": 19,
    },
    {
        "title": "并查集",
        "slug": "union-find",
        "category": "进阶基础",
        "level": "elementary",
        "difficulty_score": 6,
        "summary": "并查集用于维护动态连通关系，支持快速合并集合和查询是否同属一个集合。",
        "content_markdown": """并查集包含查找根节点和合并两个集合两个核心操作。

路径压缩和按秩合并可以让操作接近常数时间。

常见题型包括连通块数量、朋友圈、最小生成树中的 Kruskal 算法。""",
        "estimated_minutes": 55,
        "order_index": 20,
    },
    {
        "title": "最短路",
        "slug": "shortest-path",
        "category": "提高预备",
        "level": "popularization",
        "difficulty_score": 7,
        "summary": "最短路算法用于在带权图中寻找从起点到其他点的最小代价。",
        "content_markdown": """最短路入门通常从 Dijkstra 算法开始，它适用于非负权边。

学习时要理解距离数组、松弛操作和优先队列优化。

如果存在负权边，需要进一步学习 Bellman-Ford 或 SPFA 的适用条件。""",
        "estimated_minutes": 80,
        "order_index": 21,
    },
    {
        "title": "拓扑排序",
        "slug": "topological-sort",
        "category": "提高预备",
        "level": "popularization",
        "difficulty_score": 7,
        "summary": "拓扑排序用于处理有向无环图中的依赖顺序。",
        "content_markdown": """拓扑排序常用入度为 0 的点作为起点，逐步删除已经满足依赖的节点。

它适合课程安排、任务依赖、构建顺序等问题。

如果无法处理完所有节点，说明图中存在环。""",
        "estimated_minutes": 70,
        "order_index": 22,
    },
    {
        "title": "背包 DP",
        "slug": "knapsack-dp",
        "category": "提高预备",
        "level": "popularization",
        "difficulty_score": 8,
        "summary": "背包问题是动态规划的重要模型，关注容量限制下的最优选择。",
        "content_markdown": """0/1 背包中，每个物品只能选或不选；完全背包中，每个物品可以选择多次。

学习背包时要重点理解状态含义和循环顺序。循环顺序不同，表示的选择约束也不同。

背包模型可以扩展到方案数、恰好装满、多重背包等问题。""",
        "estimated_minutes": 90,
        "order_index": 23,
    },
    {
        "title": "线段树入门",
        "slug": "segment-tree-basics",
        "category": "提高预备",
        "level": "popularization",
        "difficulty_score": 8,
        "summary": "线段树用于维护区间信息，支持区间查询和区间修改的进阶数据结构。",
        "content_markdown": """线段树把区间递归拆分成左右子区间，每个节点维护一段区间的信息。

入门阶段建议先掌握单点修改和区间查询，再学习懒标记处理区间修改。

线段树代码量较大，调试时要特别注意左右边界和递归终止条件。""",
        "estimated_minutes": 90,
        "order_index": 24,
    },
]


TOPIC_DEPENDENCIES = [
    ("prefix-sum", "array-basics"),
    ("difference-array", "prefix-sum"),
    ("two-pointers", "array-basics"),
    ("binary-search", "sorting"),
    ("recursion-basics", "time-complexity"),
    ("stack-queue", "array-basics"),
    ("hash-table", "array-basics"),
    ("dfs", "recursion-basics"),
    ("bfs", "stack-queue"),
    ("greedy", "sorting"),
    ("dynamic-programming-basics", "recursion-basics"),
    ("graph-basics", "dfs"),
    ("graph-basics", "bfs"),
    ("tree-basics", "dfs"),
    ("heap-priority-queue", "array-basics"),
    ("union-find", "tree-basics"),
    ("shortest-path", "graph-basics"),
    ("shortest-path", "heap-priority-queue"),
    ("topological-sort", "graph-basics"),
    ("knapsack-dp", "dynamic-programming-basics"),
    ("segment-tree-basics", "recursion-basics"),
]


def upsert_dev_user() -> None:
    with SessionLocal() as db:
        user_id = UUID(settings.dev_user_id)
        user = db.get(User, user_id)
        values = {
            "email": "dev-user@algomentor.local",
            "username": "dev_user",
            "hashed_password": None,
            "student_id": "dev_user",
            "name": "开发用户",
            "current_level": "beginner",
            "goal_track": "self_study",
            "role": "user",
            "learning_stage": "beginner",
            "target_track": "algorithm_basics",
        }
        if user is None:
            db.add(User(id=user_id, **values))
        else:
            for key, value in values.items():
                setattr(user, key, value)
        db.commit()


def upsert_topics() -> None:
    published_at = datetime.now(timezone.utc)
    with SessionLocal() as db:
        topics_by_slug: dict[str, Topic] = {}
        for item in TOPICS:
            topic = db.scalar(select(Topic).where(Topic.slug == item["slug"]))
            values = {
                **item,
                "status": "published",
                "published_at": published_at,
            }
            if topic is None:
                topic = Topic(**values)
                db.add(topic)
            else:
                for key, value in values.items():
                    setattr(topic, key, value)
            topics_by_slug[item["slug"]] = topic
        db.flush()

        for topic_slug, depends_on_slug in TOPIC_DEPENDENCIES:
            topic = topics_by_slug[topic_slug]
            depends_on = topics_by_slug[depends_on_slug]
            existing = db.scalar(
                select(TopicDependency).where(
                    TopicDependency.topic_id == topic.id,
                    TopicDependency.depends_on_topic_id == depends_on.id,
                )
            )
            if existing is None:
                db.add(TopicDependency(topic_id=topic.id, depends_on_topic_id=depends_on.id))
        db.commit()


def main() -> None:
    upsert_dev_user()
    upsert_topics()
    print(f"Seeded dev user, {len(TOPICS)} topics, and {len(TOPIC_DEPENDENCIES)} dependencies.")


if __name__ == "__main__":
    main()
