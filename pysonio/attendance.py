
fmtStr = '{"id":%s,"date":"%s","startTime":"%s","endTime":"%s","break":"%d","comment":"%s","index":%d}'  # noqa: E501


class AttendanceRow(object):
    def __init__(self, date, start_time, end_time, break_minutes=0,
                 comment='', row_id=None, index=0):
        self.row_id = row_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.break_minutes = break_minutes
        self.comment = comment
        self.index = index

    def __repr__(self):
        return fmtStr % (
                            "null" if self.row_id is None else self.row_id,
                            self.date.strftime('%s'),
                            self.start_time.strftime('%H:%M'),
                            self.end_time.strftime('%H:%M'),
                            self.break_minutes,
                            self.comment,
                            self.index
        )


class AttendanceDay(object):
    def __init__(self, day, rows):
        self.date = day
        self._a = []
        for row in rows:
            self.add(row)

    def add(self, attendance_row):
        if attendance_row.date != self.date:
            raise ValueError('Date in AttendanceRow does not match AttendanceDay')  # noqa: E501

        self._a.append(attendance_row)
        new = []
        for idx, r in enumerate(sorted(self._a, key=lambda r: r.start_time)):
            r.index = idx
            new.append(r)
        self._a = new

    def __repr__(self):
        # Order by start_time (convenience, personio does not order it's table)
        return repr(self._a)
