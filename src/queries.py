from sqlalchemy import text

GET_PACKAGE_SCANS = text('''
use Xcelerator
SELECT SCANcode, SCANdetails, SCANlocation, aTimeStamp 
FROM OrderScans 
WHERE OrderTrackingID = :orderTrackingId''')

GET_ORDER_TRACKING_ID = text('''
use Xcelerator
SELECT OrderTrackingID 
FROM OrderPackageItems 
WHERE RefNo= :refNo
''')

GET_ORDER_EVENTS = text('''
use Xcelerator
SELECT  emlo.OrderTrackingID,
        ord.clientid,
        cm.accountno,
        emlo.EventID,
        eme.NAME,
        emlo.UserID,
        emlo.sTimeStamp,
        emlo.PackageItemID,
        emlo.ShipmentStatusCodeID
FROM   xview_eventmonitorlog_allorders emlo
       JOIN eventmonitorevents eme
         ON emlo.eventid = eme.eventid
	   JOIN orders ord 
	     ON emlo.OrderTrackingID = ord.OrderTrackingID
	   JOIN ClientMaster cm
		 ON ord.ClientID = cm.ClientID 
WHERE  emlo.ordertrackingid in :order_tracking_ids AND cm.AccountNo = :account_no AND sTimeStamp >= :timestamp AND emlo.EventID in :event_ids
order by sTimeStamp asc
''')

GET_CLIENT_ORDERS = text(''' 
use Xcelerator
select OrderTrackingID 
FROM Orders o
      JOIN ClientMaster cm 
            ON o.ClientID = cm.ClientID
      WHERE cm.AccountNo = :account_no
''')