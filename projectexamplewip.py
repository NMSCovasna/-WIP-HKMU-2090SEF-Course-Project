def shell_sort(arr):
    size = len(arr)
    gap = size // 2

    while gap > 0:
        for i in range(gap, size):
            anchor = arr[i]
            j = i
            while j >= gap and arr[j-gap] > anchor:
                arr[j] = arr[j-gap]
                j -= gap
            arr[j] = anchor
        gap = gap // 2

if __name__ == '__main__':
    elements = [61, 9, 62, 83, 37, 80, 32, 45, 93]
    shell_sort(elements)
    print(elements)