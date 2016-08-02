#! /bin/sh

DAEMON=/usr/sbin/lighttpd
DAEMON_OPTS="-f /etc/lighttpd/lighttpd.conf"

APP_PID=/var/run/lighttpd_app.pid
DB_PID=/var/run/lighttpd_db.pid
LINK_PID=/var/run/lighttpd_link.pid
ROUTER_PID=/var/run/lighttpd_router.pid
SERVER_PID=/var/run/lighttpd_serv.pid

APP_OPTS="-f /root/cemon_server/app.conf"
DB_OPTS="-f /root/cemon_server/db.conf"
LINK_OPTS="-f /root/cemon_server/link.conf"
ROUTER_OPTS="-f /root/cemon_server/routr.conf"
SERVER_OPTS="-f /root/cemon_server/serv.conf"

if ! start-stop-daemon --start  --pidfile $APP_PID --exec $DAEMON -- $APP_OPTS
then
	echo "ERROR starting APP"
	exit 1
fi

if ! start-stop-daemon --start  --pidfile $DB_PID --exec $DAEMON -- $DB_OPTS
then
        echo "ERROR starting DB"
        exit 1
fi

if ! start-stop-daemon --start  --pidfile $LINK_PID --exec $DAEMON -- $LINK_OPTS
then
        echo "ERROR starting LINK"
        exit 1
fi

if ! start-stop-daemon --start  --pidfile $ROUTER_PID --exec $DAEMON -- $ROUTER_OPTS
then
        echo "ERROR starting ROUTER"
        exit 1
fi

if ! start-stop-daemon --start  --pidfile $SERVER_PID --exec $DAEMON -- $SERVER_OPTS
then
        echo "ERROR starting SERVER"
        exit 1
fi

