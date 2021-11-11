# Functional Dependencies

Bartenders(<i>Bartender_id, First_name, Last_name, Employment_type</i>)

FD<sub>Bartenders</sub>={Bartender_id→First_name, Bartender_id→Last_name}
<p>&nbsp;</p>


CompletedOrders(<i>Order_id, Bartender_service, Completed_time</i>)

FD<sub>CompletedOrders</sub>={Order_id→Completed_time}
<p>&nbsp;</p>


EmploymentTypes(<i>Employment_id, Employment_type_desc</i>)

FD<sub>EmploymentTypes</sub>={Employment_id→Employment_type_desc}
<p>&nbsp;</p>


ItemSupplies(<i>Item_id, Item_name, Item_size, Item_price</i>)

FD<sub>ItemSupplies</sub>={Item_id→Item_name, Item_id→Item_size, Item_id→Item_price}

<i>Note: Item name does not determine item size or item price becuase duplicate items may exist. Although the GUI interface will restrict duplicates, database interaction may introduce duplicate items.</i>
<p>&nbsp;</p>


OrderableItems(<i>Item_id, Item_name, Item_price, Available</i>)

FD<sub>OrderableItems</sub>={Item_id→Item_name, Item_id→Item_price}

<i>Note: Item name does not determine item price or availability becuase duplicate items may exist. Although the GUI interface will restrict duplicates, database interaction may introduce duplicate items.</i>
<p>&nbsp;</p>


Orders(<i>Order_id, Order_item, Order_time</i>)

FD<sub>Orders</sub>={Order_id→Order_item, Order_id→Order_time}
<p>&nbsp;</p>


Recipes(<i>Finished_item_id, Supply_item_id, Recipe_amount</i>)

FD<sub>Recipes</sub>={(Finished_item_id, Supply_item_id)→Recipe_amount}
