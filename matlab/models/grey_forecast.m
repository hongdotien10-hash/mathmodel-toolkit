function result = grey_forecast(data, forecast_steps)
% GREY_FORECAST 灰色预测 GM(1,1) 模型
%   data: 原始非负时序数据 (向量)
%   forecast_steps: 预测步数
%
%   result: struct 包含:
%       .forecast: 预测值向量
%       .fitted: 拟合值向量
%       .a: 发展系数
%       .b: 灰色作用量
%       .mape: 平均绝对百分比误差
%       .c_ratio: 后验差比值
%       .p_value: 小误差概率
%       .grade: 精度等级字符串
%
% 示例:
%   r = grey_forecast([10 15 20 26 33], 3);
%   disp(r.forecast);

    if nargin < 2
        forecast_steps = 1;
    end

    x0 = data(:)';  % 转为行向量
    n = length(x0);

    % 1-AGO 累加生成
    x1 = cumsum(x0);

    % 背景值序列
    z = (x1(1:end-1) + x1(2:end)) / 2;

    % 最小二乘估计
    B = [-z', ones(n-1, 1)];
    Y = x0(2:end)';
    params = (B' * B) \ (B' * Y);
    a = params(1);
    b = params(2);

    % 时间响应函数
    predict_ago = @(k) (x0(1) - b/a) * exp(-a * k) + b/a;

    % 拟合
    fitted_ago = arrayfun(predict_ago, 0:n-1);
    fitted = [x0(1), diff(fitted_ago)];

    % 预测
    forecast_ago = arrayfun(predict_ago, n:n+forecast_steps-1);
    forecast = [fitted_ago(end), diff(forecast_ago)];
    forecast = forecast(2:end);  % 去掉第一个（是 last_fitted）

    % 精度评估
    residual = x0 - fitted;
    mape = mean(abs(residual ./ (x0 + 1e-10))) * 100;

    s1 = std(x0);
    s2 = std(residual);
    c_ratio = s2 / max(s1, 1e-10);

    p_count = sum(abs(residual - mean(residual)) < 0.6745 * s1);
    p_value = p_count / n;

    % 精度等级
    if c_ratio < 0.35 && p_value > 0.95
        grade = '一级（优）';
    elseif c_ratio < 0.5 && p_value > 0.8
        grade = '二级（合格）';
    elseif c_ratio < 0.65 && p_value > 0.7
        grade = '三级（勉强）';
    else
        grade = '四级（不合格）';
    end

    % 返回结果
    result.forecast = forecast;
    result.fitted = fitted;
    result.a = a;
    result.b = b;
    result.mape = mape;
    result.c_ratio = c_ratio;
    result.p_value = p_value;
    result.grade = grade;
end
