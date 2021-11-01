-- Create Orders Table
CREATE TABLE Orders(
    Order_id INT PRIMARY KEY,
    Order_item INT NOT NULL,
    Order_time datetime NOT NULL);

-- Create Orderable Items Table
CREATE TABLE OrderableItems(
    Item_id INT PRIMARY KEY,
    Item_name VARCHAR(100) NOT NULL,
    Item_price DECIMAL(4,2) NOT NULL,
    Available TINYINT NOT NULL);

-- Create Recipes Table
CREATE TABLE Recipes(
    Finished_item_id INT NOT NULL,
    Supply_item_id INT NOT NULL,
    Recipe_amount INT NOT NULL,
    PRIMARY KEY (Finished_item_id, Supply_item_id));

-- Create Item Supplies Table
CREATE TABLE ItemSupplies(
    Item_id INT PRIMARY KEY,
    Item_name VARCHAR(100) NOT NULL,
    Item_size INT NULL,
    Item_price DECIMAL(5, 2) NULL);

-- Create Bartenders Table
 CREATE TABLE Bartenders(
    Bartender_id INT PRIMARY KEY,
    First_name VARCHAR(100) NULL,
    Last_name VARCHAR(100) NULL,
    Employment_type INT NOT NULL);

-- Create Completed Orders Table
CREATE TABLE CompletedOrders(
    Order_id INT PRIMARY KEY,
    Bartender_service INT NULL,
    Completed_time datetime NOT NULL);

-- Create Employment Types Lookup Table
CREATE TABLE EmploymentTypes(
    Employment_id INT PRIMARY KEY,
    Employment_type_desc VARCHAR(15) NOT NULL);

-- Insert values into Employment Types Lookup Table
INSERT INTO EmploymentTypes VALUES
    (1, 'Full Time'),
    (2, 'Part Time'),
    (3, 'Unemployed');

-----
-- Foreign Key Constraints
-----
-- When a employment type is deleted, set Bartender employment type to NULL
ALTER TABLE Bartenders
    ADD CONSTRAINT employmentConstraint
    FOREIGN KEY (Employment_type)
    REFERENCES EmploymentTypes(Employment_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- When a bartender is deleted, set the Completed Order Bartender service to NULL
ALTER TABLE CompletedOrders
	ADD CONSTRAINT bartenderCompletedOrderConstraint
    FOREIGN KEY (Bartender_service)
    REFERENCES Bartenders(Bartender_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- When a Orderable Item is deleted NULL it in the Orders table
ALTER TABLE Orders
 ADD CONSTRAINT OrdersOrderableItemsConstraint
 FOREIGN KEY (Order_item)
 REFERENCES OrderableItems(Item_id)
 ON DELETE SET NULL
 ON UPDATE CASCADE;




-- View attribute domains
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.columns where table_schema='dcaramel_1';
SELECT * FROM information_schema.TABLE_CONSTRAINTS WHERE INFORMATION_SCHEMA.TABLE_CONSTRAINTS.CONSTRAINT_TYPE='FOREIGN KEY' AND information_schema.TABLE_CONSTRAINTS.TABLE_NAME='CompletedOrders';
ALTER TABLE mytable MODIFY mycolumn varchar(255) null;
-- When Deleted from Orders, not deleted in CompletedOrders because cannot make ON DELEtE CASCADE move in both directions