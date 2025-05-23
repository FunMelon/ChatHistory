from typing import List, Any, Tuple


def dyn_select_top_k(
    score: List[Tuple[Any, float]], jmp_factor: float, var_factor: float
) -> List[Tuple[Any, float, float]]:
    """动态TopK选择"""
    # 按照分数排序（降序）
    sorted_score = sorted(score, key=lambda x: x[1], reverse=True)

    # 归一化
    max_score = sorted_score[0][1]
    min_score = sorted_score[-1][1]
    normalized_score = []
    for score_item in sorted_score:
        normalized_score.append(
            tuple(
                [
                    score_item[0],
                    score_item[1],
                    (score_item[1] - min_score) / (max_score - min_score),
                ]
            )
        )

    # 寻找跳变点：score变化最大的位置
    jump_idx = 0
    for i in range(1, len(normalized_score)):
        if abs(normalized_score[i][2] - normalized_score[i - 1][2]) > abs(
            normalized_score[jump_idx][2] - normalized_score[jump_idx - 1][2]
        ):
            jump_idx = i
    # 跳变阈值
    jump_threshold = normalized_score[jump_idx][2]

    # 计算均值
    mean_score = sum([s[2] for s in normalized_score]) / len(normalized_score)
    # 计算方差
    var_score = sum([(s[2] - mean_score) ** 2 for s in normalized_score]) / len(
        normalized_score
    )

    # 动态阈值
    threshold = jmp_factor * jump_threshold + (1 - jmp_factor) * (
        mean_score + var_factor * var_score
    )

    # 重新过滤
    res = [s for s in normalized_score if s[2] > threshold]

    return res

def dyn_select_top_k_with_keywords(
    score: List[Tuple[str, float]],
    jmp_factor: float = 0.5,
    var_factor: float = 1.0,
    keywords: List[str] = None,
) -> List[Tuple[str, float, float]]:
    """
    动态TopK选择 + 关键词强制保留（仅保留命中关键词的最高得分项）

    :param score: [(text, score)]
    :param jmp_factor: 跳变点与均值-方差融合的加权因子，范围[0,1]
    :param var_factor: 方差放大因子
    :param keywords: 必须保留的关键词列表，命中则从中只保留最高得分项
    :return: [(text, raw_score, normalized_score)]
    """
    """动态TopK选择，增加关键词强制保留最高相似度项"""

    # 1. 按照分数排序（降序）
    sorted_score = sorted(score, key=lambda x: x[1], reverse=True)

    # 2. 归一化
    max_score = sorted_score[0][1]
    min_score = sorted_score[-1][1]
    # 防止max_score==min_score导致除零错误
    denom = max_score - min_score if max_score != min_score else 1e-8

    normalized_score = []
    for score_item in sorted_score:
        normalized_score.append(
            (
                score_item[0],
                score_item[1],
                (score_item[1] - min_score) / denom,
            )
        )

    # 3. 寻找跳变点：score变化最大的位置
    jump_idx = 1
    max_jump = abs(normalized_score[1][2] - normalized_score[0][2])
    for i in range(2, len(normalized_score)):
        jump = abs(normalized_score[i][2] - normalized_score[i - 1][2])
        if jump > max_jump:
            max_jump = jump
            jump_idx = i
    jump_threshold = normalized_score[jump_idx][2]

    # 4. 计算均值与方差
    mean_score = sum(s[2] for s in normalized_score) / len(normalized_score)
    var_score = sum((s[2] - mean_score) ** 2 for s in normalized_score) / len(normalized_score)

    # 5. 计算动态阈值
    threshold = jmp_factor * jump_threshold + (1 - jmp_factor) * (mean_score + var_factor * var_score)

    # 6. 过滤结果（保留分数高于阈值的）
    filtered = [s for s in normalized_score if s[2] > threshold]

    # 7. 关键词强制保留：只保留相似度最高的那个关键词项
    if keywords:
        keyword_candidates = [
            s for s in normalized_score
            if any(k in str(s[0]) for k in keywords)  # 转成字符串检查关键词
        ]
        if keyword_candidates:
            top_keyword_hit = max(keyword_candidates, key=lambda x: x[1])  # 选最高原始分数
            if top_keyword_hit not in filtered:
                filtered.append(top_keyword_hit)

    # 8. 返回结果
    return filtered