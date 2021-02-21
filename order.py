class Orders(object):
    def __init__(self, userid, username, ordernum, item, timeslot, timestamp, address, regionid):
        self.userid = userid
        self.username = username
        self.ordernum = ordernum
        self.item = item
        self.timeslot = timeslot
        self.timestamp = timestamp
        self.address = address
        self.regionid = regionid

    @staticmethod
    def orders_from_dict(source):
        order = Orders(source[u'userid'], source[u'username'], source[u'ordernum'], source[u'item'], source[u'timeslot'], source[u'timestamp'], source[u'address'])
        return order

    def orders_to_dict(self):
        orderdata = {
            u'userid': self.userid,
            u'username': self.username,
            u'ordernum': self.ordernum,
            u'item': self.item,
            u'timeslot': self.timeslot,
            u'timestamp': self.timestamp,
            u'address' : self.address,
            u'regionid': self.regionid
        }
        return orderdata

    def __repr__(self):
        return(
            f'userid={self.userid}, \
                username={self.username}, \
                ordernum={self.ordernum},\
                item={self.item}, \
                timeslot={self.timeslot},\
                timestamp={self.timestamp},\
                address = {self.address},\
                regionid = {self.regionid}'
        )