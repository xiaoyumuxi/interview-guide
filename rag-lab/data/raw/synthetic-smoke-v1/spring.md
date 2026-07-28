# Spring 工程笔记

## Spring 事务传播

Spring 事务传播的第一项机制围绕 `REQUIRES_NEW` 展开。系统先识别请求的边界与状态，再用 REQUIRES_NEW 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D1-A 用于区分本段事实。

Spring 事务传播的第二项机制使用 `TransactionSynchronization` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 TransactionSynchronization 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D1-B 用于区分这一证据。

## Bean 生命周期

Bean 生命周期的第一项机制围绕 `BeanPostProcessor` 展开。系统先识别请求的边界与状态，再用 BeanPostProcessor 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D2-A 用于区分本段事实。

Bean 生命周期的第二项机制使用 `InitializingBean` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 InitializingBean 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D2-B 用于区分这一证据。

## 循环依赖

循环依赖的第一项机制围绕 `singletonFactories` 展开。系统先识别请求的边界与状态，再用 singletonFactories 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D3-A 用于区分本段事实。

循环依赖的第二项机制使用 `early-reference` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 early-reference 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D3-B 用于区分这一证据。

## Spring AI 结构化输出

Spring AI 结构化输出的第一项机制围绕 `StructuredOutputConverter` 展开。系统先识别请求的边界与状态，再用 StructuredOutputConverter 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D4-A 用于区分本段事实。

Spring AI 结构化输出的第二项机制使用 `retry` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 retry 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D4-B 用于区分这一证据。

## Web MVC 异常处理

Web MVC 异常处理的第一项机制围绕 `ControllerAdvice` 展开。系统先识别请求的边界与状态，再用 ControllerAdvice 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D5-A 用于区分本段事实。

Web MVC 异常处理的第二项机制使用 `ExceptionHandler` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 ExceptionHandler 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D5-B 用于区分这一证据。
