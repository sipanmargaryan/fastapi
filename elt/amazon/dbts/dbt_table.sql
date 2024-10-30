{{ config(materialized='table') }}
with source_data as (
    SELECT "Index",
           "Industry",
           "Founded",
           "Country",
           "Number of employees"::INT * 2 as "Number of employees"
    from test
)
select * from source_data