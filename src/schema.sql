use CDLData



CREATE TABLE TrackingUserType (
    tracking_user_type_id INT IDENTITY(1,1) PRIMARY KEY,
    user_type VARCHAR(50) NOT NULL,
    date_created DATETIME NOT NULL,
	date_modified DATETIME,
	active INT default 1
);

CREATE TABLE TrackingUser(
	tracking_user_id INT IDENTITY(1,1) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(200) NOT NULL,
    hash_password VARCHAR(255) NOT NULL,
    tracking_user_type_id  INT NOT NULL,
    date_created DATETIME NOT NULL,
    date_modified DATETIME,
    active INT default 1
);

CREATE TABLE TrackingUserAccount(
	tracking_user_account_id INT IDENTITY(1,1) PRIMARY KEY,
    tracking_user_id  INT NOT NULL,
	account_no VARCHAR(18) NOT NULL,
    date_created DATETIME NOT NULL,
    date_modified DATETIME,
    active INT default 1
);

CREATE TABLE TrackingSubscription (
    tracking_subscription_id INT IDENTITY(1,1) PRIMARY KEY,
    account_no VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
	order_tracking_ids TEXT,
	active INT default 1
);


    
