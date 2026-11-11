# ADT

In functional programming (FP), ADT stands for Algebraic Data Type (not to be confused with Abstract Data Type, which is a different computer science concept). [1] (https://medium.com/@jnkrtech/abstract-data-types-and-objects-17828bd4abdc)
An algebraic data type is a composite data type built by combining simpler types together. They are called "algebraic" because you can combine them using two primary operations—product and sum—which behave much like multiplication and addition in algebra. [1] (https://en.wikipedia.org/wiki/Algebraic_data_type), [2] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf)

## Core Types of ADTs


1. Product Types (The "AND" Combination)

• What it is: A data structure that holds multiple values at the same time.
• How it works: If type A has x possible values and type B has y possible values, a product type containing both has x × y possible values.
• Examples: Tuples, records, structs, or classes with multiple fields (e.g., a Point with an x: Float and a y: Float). [1] (https://rockthejvm.com/articles/algebraic-data-types-in-java), [2] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf), [3] (https://en.wikipedia.org/wiki/Algebraic_data_type)

2. Sum Types / Tagged Unions (The "OR" Combination)

• What it is: A data structure that holds one of several possible variants at any given time, tagged with an identifier. [1] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf), [2] (https://en.wikipedia.org/wiki/Algebraic_data_type), [3] (https://rockthejvm.com/articles/algebraic-data-types-in-java)
• How it works: If type A has x values and type B has y values, a sum type of A or B has x + y possible values. [1] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf)
• Examples:
• Option / Maybe (either Some(value) or None).
• Either / Result (either Left(Error) or Right(Success)).
• Custom state enums (e.g., a payment state that is either CreditCard(details) or Paypal(email) or Cash). [1] (https://rockthejvm.com/articles/algebraic-data-types-in-java), [2] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf)

## Why ADTs Matter in FP

• Making illegal states unrepresentable: By combining sum and product types, you design data models where invalid combinations cannot even be instantiated. [1] (https://rockthejvm.com/articles/algebraic-data-types-in-scala), [2] (https://rockthejvm.com/articles/algebraic-data-types-in-java)
• Compiler exhaustiveness checking: When you consume an ADT using pattern matching (e.g., switch or match expressions), the compiler forces you to handle every single variant. If you miss one, it throws a compile-time error. [1] (https://en.wikipedia.org/wiki/Algebraic_data_type), [2] (https://rockthejvm.com/articles/algebraic-data-types-in-java)
• Replacing null/exceptions: Instead of throwing runtime errors or returning ambiguous null values, FP uses sum types like Option or Result to make success or failure explicit in the type signature. [1] (https://rockthejvm.com/articles/algebraic-data-types-in-java), [2] (https://dev.to/gcanti/functional-design-algebraic-data-types-36kf)
Read more about structural modeling on the Algebraic Data Type Wikipedia Page. [1] (https://en.wikipedia.org/wiki/Algebraic_data_type)
Would you like to see how ADTs are written in a specific language (like TypeScript, Rust, Scala, or Swift), or focus on how to use pattern matching with them?
