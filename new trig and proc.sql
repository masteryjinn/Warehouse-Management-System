-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE return_product(IN order_detail_id INT)
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_product_id INT;
    DECLARE v_quantity INT;
    
    -- Отримуємо дані з таблиці OrderDetails
    SELECT order_id, product_id, quantity 
    INTO v_order_id, v_product_id, v_quantity
    FROM OrderDetails
    WHERE order_detail_id = order_detail_id;

    -- Перевірка, чи існує запис
    IF v_order_id IS NULL OR v_product_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'OrderDetail not found';
    END IF;

    -- Повертаємо товар на склад
    UPDATE Products
    SET quantity = quantity + v_quantity
    WHERE product_id = v_product_id;

    -- Оновлюємо статус замовлення на 'processing', якщо необхідно
    UPDATE Orders
    SET status = 'processing'
    WHERE order_id = v_order_id;

    -- Оновлення статусу історії замовлення
    INSERT INTO OrderStatusHistory (order_id, status, changed_at)
    VALUES (v_order_id, 'processing', CURRENT_TIMESTAMP);
END$$

DELIMITER ;
 -- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER log_status_change
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO OrderStatusHistory (order_id, status, changed_at)
        VALUES (NEW.order_id, NEW.status, CURRENT_TIMESTAMP);
    END IF;
END$$

DELIMITER ;
-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE create_order(
    IN customer_id INT, 
    IN order_status VARCHAR(50),
    IN products JSON
)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE num_items INT;
    DECLARE current_product_id INT;
    DECLARE current_quantity INT;
    DECLARE current_price DECIMAL(10,2);
    DECLARE order_id INT;

    -- Вставляємо нове замовлення
    INSERT INTO Orders (customer_id, status)
    VALUES (customer_id, order_status);
    
    SET order_id = LAST_INSERT_ID();

    -- Одержуємо кількість елементів у масиві
    SET num_items = JSON_LENGTH(products);

    WHILE i < num_items DO
        SET current_product_id = JSON_UNQUOTE(JSON_EXTRACT(products, CONCAT('$[', i, '].product_id')));
        SET current_quantity = JSON_UNQUOTE(JSON_EXTRACT(products, CONCAT('$[', i, '].quantity')));
        SET current_price = JSON_UNQUOTE(JSON_EXTRACT(products, CONCAT('$[', i, '].price')));

        INSERT INTO OrderDetails (order_id, product_id, quantity, price)
        VALUES (order_id, current_product_id, current_quantity, current_price);

        SET i = i + 1;
    END WHILE;
END$$

DELIMITER ;
-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER restore_stock_before_order_delete
BEFORE DELETE ON Orders
FOR EACH ROW
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_product_id INT;
    DECLARE v_quantity INT;
    DECLARE v_storage_section_id INT;
    DECLARE v_packaging_section_id INT;
    DECLARE v_status VARCHAR(50);

    DECLARE cur CURSOR FOR
        SELECT product_id, quantity
        FROM OrderDetails
        WHERE order_id = OLD.order_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    SET v_status = OLD.status;

    IF v_status IN ('new', 'processing') THEN
        -- Знаходимо секцію пакування
        SELECT section_id INTO v_packaging_section_id
        FROM WarehouseSections
        WHERE section_type = 'packaging'
        LIMIT 1;

        OPEN cur;

        read_loop: LOOP
            FETCH cur INTO v_product_id, v_quantity;
            IF done THEN
                LEAVE read_loop;
            END IF;

            -- Отримуємо секцію, де має зберігатися продукт
            SELECT section_id INTO v_storage_section_id
            FROM Products
            WHERE product_id = v_product_id;

            -- Повертаємо товар на склад (оновлюємо кількість)
            UPDATE Products
            SET quantity = quantity + v_quantity
            WHERE product_id = v_product_id;

            -- Записуємо рух товару: виїхав з пакувальної
            INSERT INTO StockMovements (product_id, movement_type, quantity, section_id, movement_reason)
            VALUES (v_product_id, 'out', v_quantity, v_packaging_section_id, 'Повернення на склад після скасування замовлення');

            -- Записуємо рух товару: в'їхав у зберігальну
            INSERT INTO StockMovements (product_id, movement_type, quantity, section_id, movement_reason)
            VALUES (v_product_id, 'in', v_quantity, v_storage_section_id, 'Повернення на склад після скасування замовлення');
        END LOOP;

        CLOSE cur;
    END IF;
END$$

DELIMITER ;


DELIMITER ;
-- -----------------------------------------------------------------------------------------------------------
-- -----------------------------------------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER prevent_multiple_packaging_sections
BEFORE INSERT ON WarehouseSections
FOR EACH ROW
BEGIN
    DECLARE section_count INT;
    -- Перевірка, чи вже існує секція пакування
    SELECT COUNT(*) INTO section_count
    FROM WarehouseSections
    WHERE section_type = 'packaging';

    -- Якщо секція пакування вже існує, запобігти додаванню нової
    IF section_count > 0 AND NEW.section_type = 'packaging' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only one packaging section is allowed';
    END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER record_stock_on_order_detail_insert
AFTER INSERT ON OrderDetails
FOR EACH ROW
BEGIN
    DECLARE v_section_id INT;
    DECLARE v_packaging_section_id INT;

    -- Отримуємо поточну секцію продукту
    SELECT section_id INTO v_section_id
    FROM Products
    WHERE product_id = NEW.product_id;

    -- Знаходимо ID секції пакування
    SELECT section_id INTO v_packaging_section_id
    FROM WarehouseSections
    WHERE section_type = 'packaging' LIMIT 1;

    -- Переміщаємо товар до секції пакування
    INSERT INTO StockMovements (product_id, movement_type, quantity, section_id, movement_reason)
    VALUES (NEW.product_id, 'out', NEW.quantity, v_section_id, 'Переміщення в секціїю пакування');  -- Виводимо з початкової секції

    INSERT INTO StockMovements (product_id, movement_type, quantity, section_id, movement_reason)
    VALUES (NEW.product_id, 'in', NEW.quantity, v_packaging_section_id, 'Переміщення в секціїю пакування');

    -- Оновлюємо кількість товару на складі
    UPDATE Products
    SET quantity = quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
END$$

DELIMITER ;
-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER record_shipment_after_status_change
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_product_id INT;
    DECLARE v_quantity INT;
    DECLARE v_packaging_section_id INT;

    DECLARE cur CURSOR FOR
        SELECT product_id, quantity
        FROM OrderDetails
        WHERE order_id = OLD.order_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Перевіряємо, чи статус змінився на 'shipped'
    IF OLD.status != 'shipped' AND NEW.status = 'shipped' THEN
        -- Знаходимо секцію пакування та секцію відправки
        SELECT section_id INTO v_packaging_section_id
        FROM WarehouseSections
        WHERE section_type = 'packaging' LIMIT 1;

        OPEN cur;

        read_loop: LOOP
            FETCH cur INTO v_product_id, v_quantity;
            IF done THEN
                LEAVE read_loop;
            END IF;

            -- Переміщаємо товар з секції пакування в секцію для відправки
            INSERT INTO StockMovements (product_id, movement_type, quantity, section_id, movement_reason)
            VALUES (v_product_id, 'out', v_quantity, v_packaging_section_id, 'Відправка зі складу');  -- Виводимо з секції пакування

        END LOOP;

        CLOSE cur;
    END IF;
END$$

DELIMITER ;
-- --------------------------------------------------------------------------------------------------
-- --------------------------------------------------------------------------------------------------
