function result = topsis(matrix, weights, impacts)
% TOPSIS 优劣解距离法
%   matrix: 决策矩阵 (m方案 × n指标)
%   weights: 指标权重 (1×n 向量)
%   impacts: 指标方向，1=正向，-1=负向 (1×n 向量)
%
%   result: struct 包含:
%       .scores: 相对贴近度 (1×m)
%       .rank: 排名 (1×m)
%       .d_plus: 到正理想解距离
%       .d_minus: 到负理想解距离
%
% 示例:
%   m = [1 2; 3 4; 5 6];
%   r = topsis(m, [0.5 0.5], [1 1]);
%   disp(r.scores);

    if nargin < 3
        impacts = ones(1, size(matrix, 2));
    end

    [m, n] = size(matrix);
    weights = weights(:)' / sum(weights);

    % Step 1: 向量归一化
    norm_col = sqrt(sum(matrix.^2, 1));
    norm_col(norm_col == 0) = 1;
    normalized = matrix ./ norm_col;

    % Step 2: 加权
    weighted = normalized .* weights;

    % Step 3: 正负理想解
    ideal_best = zeros(1, n);
    ideal_worst = zeros(1, n);
    for j = 1:n
        col = weighted(:, j);
        if impacts(j) > 0
            ideal_best(j) = max(col);
            ideal_worst(j) = min(col);
        else
            ideal_best(j) = min(col);
            ideal_worst(j) = max(col);
        end
    end

    % Step 4: 距离
    d_plus = sqrt(sum((weighted - ideal_best).^2, 2));
    d_minus = sqrt(sum((weighted - ideal_worst).^2, 2));

    % Step 5: 相对贴近度
    scores = d_minus ./ (d_plus + d_minus + 1e-10);
    [~, idx] = sort(scores, 'descend');
    rank = zeros(m, 1);
    for i = 1:m
        rank(idx(i)) = i;
    end

    result.scores = scores';
    result.rank = rank';
    result.d_plus = d_plus';
    result.d_minus = d_minus';
end
