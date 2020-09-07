class Users(object):
    def __init__(self, userid, username, firstname, address, unit, postal, latitude, longitude, timestamp):
        self.userid = userid
        self.username = username
        self.firstname = firstname
        self.address = address
        self.unit = unit
        self.postal = postal
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp = timestamp

    @staticmethod
    def users_from_dict(source):
        users = Users(source[u'userid'], source[u'username'], source[u'firstname'], source[u'address'], source[u'unit'], source[u'postal'], source[u'latitude'], source[u'longitude'], source[u'timestamp'])
        return users

    def users_to_dict(self):
        userdata = {
            u'userid': self.userid,
            u'username': self.username,
            u'firstname': self.firstname,
            u'address': self.address,
            u'unit': self.unit,
            u'postal': self.postal,
            u'latitude': self.latitude,
            u'longitude': self.longitude,
            u'timestamp': self.timestamp
        }
        return userdata

    def __repr__(self):
        return(
            f'userid={self.userid}, \
                username={self.username}, \
                firstname={self.firstname}, \
                address={self.address}, \
                unit={self.unit},\
                postal={self.postal},\
                latitude={self.latitude},\
                longitude={self.longitude},\
                timestamp= {self.timestamp}'
        )