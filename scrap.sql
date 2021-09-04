Select COUNT(*), DATE_FORMAT(Created_At,"%Y-%m") as Month_Group FROM Order_Date GROUP BY Month_Group


Select SUM(*), DATE_FORMAT(Created_At,"%Y-%m") as Month_Group FROM Order_Date GROUP BY Month_Group


SELECT
    DATEPART(hour, Order_Date) AS HOUR, COUNT(*)
FROM TABLE
GROUP BY DATEPART(week, RegistrationDate)
ORDER BY DATEPART(week, RegistrationDate);

-- https://www.w3schools.com/sql/func_sqlserver_datepart.asp