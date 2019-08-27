def get_full_child_count(node):
    sum_new_size = 1
    initial_depth = 1
    depth = 0
    for child in node.children:
        new_size, new_depth = get_full_child_count(child)
        depth = max(depth, new_depth)
        sum_new_size += new_size

    return sum_new_size, (initial_depth + depth)
