# 解题思路

使用前缀和预处理数组。

定义 `prefix[i]` 表示前 `i` 个元素的总和：

```text
prefix[0] = 0
prefix[i] = prefix[i - 1] + a[i]
```

区间 `[l, r]` 的和为：

```text
prefix[r] - prefix[l - 1]
```

预处理需要 `O(n)` 时间，每次查询需要 `O(1)` 时间，因此总时间复杂度为 `O(n + q)`，空间复杂度为 `O(n)`。

由于数组元素和区间和可能较大，C++ 应使用 `long long`，Python 整数可直接使用。

## C++17 标准程序

```cpp
#include <iostream>
#include <vector>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    int q;
    cin >> n >> q;

    vector<long long> prefix(n + 1, 0);
    for (int i = 1; i <= n; ++i) {
        long long value;
        cin >> value;
        prefix[i] = prefix[i - 1] + value;
    }

    while (q--) {
        int left;
        int right;
        cin >> left >> right;
        cout << prefix[right] - prefix[left - 1] << '\n';
    }

    return 0;
}
```

## Python 3.11 标准程序

```python
import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    iterator = iter(data)

    n = next(iterator)
    q = next(iterator)

    prefix = [0] * (n + 1)
    for index in range(1, n + 1):
        prefix[index] = prefix[index - 1] + next(iterator)

    answers: list[str] = []
    for _ in range(q):
        left = next(iterator)
        right = next(iterator)
        answers.append(str(prefix[right] - prefix[left - 1]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()
```
