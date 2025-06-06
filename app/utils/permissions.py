class Permission:
    # Basic permissions
    VIEW_EVENTS = 0x01          # 1
    BOOK_TICKET = 0x02          # 2
    CANCEL_TICKET = 0x04        # 4
    VIEW_OWN_BOOKINGS = 0x08    # 8
    
    # Staff permissions
    MANAGE_EVENTS = 0x10        # 16
    VIEW_ALL_BOOKINGS = 0x20    # 32
    MANAGE_BOOKINGS = 0x40      # 64
    
    # Admin permissions
    VIEW_DASHBOARD = 0x80       # 128
    VIEW_REPORTS = 0x100        # 256
    MANAGE_USERS = 0x200        # 512
    MANAGE_ROLES = 0x400        # 1024

    # Role permissions
    USER = (VIEW_EVENTS |
           BOOK_TICKET |
           CANCEL_TICKET |
           VIEW_OWN_BOOKINGS)

    STAFF = (USER |
            MANAGE_EVENTS |
            VIEW_ALL_BOOKINGS |
            MANAGE_BOOKINGS |
            VIEW_DASHBOARD)

    ADMIN = 0xFFF  # All permissions

    @staticmethod
    def get_permission_names():
        """Get a dictionary of permission names and their values"""
        return {
            'VIEW_EVENTS': Permission.VIEW_EVENTS,
            'BOOK_TICKET': Permission.BOOK_TICKET,
            'CANCEL_TICKET': Permission.CANCEL_TICKET,
            'VIEW_OWN_BOOKINGS': Permission.VIEW_OWN_BOOKINGS,
            'MANAGE_EVENTS': Permission.MANAGE_EVENTS,
            'VIEW_ALL_BOOKINGS': Permission.VIEW_ALL_BOOKINGS,
            'MANAGE_BOOKINGS': Permission.MANAGE_BOOKINGS,
            'VIEW_DASHBOARD': Permission.VIEW_DASHBOARD,
            'VIEW_REPORTS': Permission.VIEW_REPORTS,
            'MANAGE_USERS': Permission.MANAGE_USERS,
            'MANAGE_ROLES': Permission.MANAGE_ROLES
        } 