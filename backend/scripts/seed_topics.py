from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import UUID

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.topic import Topic
from app.models.user import User


TOPICS = [
    {
        "title": "时间复杂度",
        "slug": "time-complexity",
        "category": "基础阶段",
        "level": "beginner",
        "difficulty_score": 2,
        "summary": "理解算法运行时间如何随输入规模增长，是判断做法能否通过的基础。",
        "content_markdown": """时间复杂度关注的是输入规模 n 变大时，算法步骤数量的增长趋势。

常见复杂度从低到高包括 O(1)、O(log n)、O(n)、O(n log n)、O(n^2)。学习时重点不是背公式，而是能从循环、递归和数据范围判断一个做法是否可行。

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

学习数组时要特别注意下标从 0 还是 1 开始、循环边界是否包含末尾，以及修改数组时是否影响后续判断。

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
        "content_markdown": """字符串可以看作字符数组，但它还有长度、拼接、切片等语言内置操作。

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
        "summary": "排序能把数据调整为有序状态，常作为后续贪心、双指针和二分的前置步骤。",
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
        "content_markdown": """前缀和数组 pre[i] 表示前 i 个元素的总和。区间 [l, r] 的和可以通过两个前缀相减得到。

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
        "content_markdown": """差分数组记录相邻元素之间的变化。对区间 [l, r] 加上一个值，只需要修改两个边界位置。

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
        "category": "进阶基础",
        "level": "beginner",
        "difficulty_score": 5,
        "summary": "递归把问题拆成更小的同类问题，是 DFS、分治和动态规划的重要基础。",
        "content_markdown": """递归函数通常包含两个部分：递归终止条件，以及把当前问题拆成子问题的递推逻辑。

写递归时要先明确函数含义，再设计边界条件，最后考虑每一层如何向下一层推进。

常见风险包括忘记终止条件、递归层数过深、重复计算过多。""",
        "estimated_minutes": 50,
        "order_index": 10,
    },
]


def upsert_dev_user() -> None:
    with SessionLocal() as db:
        user_id = UUID(settings.dev_user_id)
        user = db.get(User, user_id)
        if user is None:
            db.add(
                User(
                    id=user_id,
                    email="dev-user@algomentor.local",
                    username="dev_user",
                    hashed_password=None,
                    student_id="dev_user",
                    name="开发用户",
                    current_level="beginner",
                    goal_track="self_study",
                    learning_stage="beginner",
                    target_track="algorithm_basics",
                )
            )
            db.commit()


def upsert_topics() -> None:
    published_at = datetime.now(timezone.utc)
    with SessionLocal() as db:
        for item in TOPICS:
            topic = db.scalar(select(Topic).where(Topic.slug == item["slug"]))
            values = {
                **item,
                "status": "published",
                "published_at": published_at,
            }
            if topic is None:
                db.add(Topic(**values))
            else:
                for key, value in values.items():
                    setattr(topic, key, value)
        db.commit()


def main() -> None:
    upsert_dev_user()
    upsert_topics()
    print(f"Seeded dev user and {len(TOPICS)} topics.")


if __name__ == "__main__":
    main()
