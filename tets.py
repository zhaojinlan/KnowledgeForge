def calculate_square(x):
    """计算一个数的平方"""
    result = x * x
    print(f"{x} 的平方是: {result}")
    return result


def main():
    print("程序开始运行...")

    a = 5
    b = 3

    # 打一个断点试试

    sum_result = a + b
    print(f"加法结果: {sum_result}")

    # 循环中调用函数
    numbers = [1, 2, 3, 4, 5]
    squares = []
    for num in numbers:
        sq = calculate_square(num)
        squares.append(sq)

    # 条件判断
    if sum_result > 6:
        print("和大于 6，执行额外操作")
        sum_result *= 2

    print(f"最终结果: {sum_result}")
    print("程序结束。")


# 运行主函数
if __name__ == "__main__":
    main()
