#!/usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without #
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

_hermes_svn_id_="$Id$"

import sys,os.path,_thread,time,inspect
import flask
#import flask_sqlalchemy

# import i18n
# import gettext
# 
# inlizer = i18n.i18n('locale')
# translateString=inlizer.translateString

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
#import site_info
#sI = site_info.SiteInfo()
#try:
#    cwd = os.path.dirname(__file__)
#    if cwd not in sys.path:
#        sys.path.append(cwd)
#
#    if sI.srcDir() not in sys.path:
#        sys.path.append(sI.srcDir())
#except:
#    pass

from sqlalchemy import Column, Integer, String, PickleType, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.ext.declarative import declarative_base
# import db_routines
# import privs
# from user_fs import HermesUserFS
# import crumbtracks

SESSION = None

Base = declarative_base()

class UISessionException(Exception):
    pass

class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

#        if isinstance(value, dict) and not isinstance(value,MutableDict):
#            dict.__setitem__(self, key, MutableDict(value))
#        else:
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()
        
    def clear(self):
        dict.clear(self)
        self.changed()
        
    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        self.update(state)

class LockedState:
    """
    This should really be an inner class of UISession, but I don't know if that
    would confuse SQLAlchemy
    """
    def __init__(self, uiSession):
        self.uiSession = uiSession
        self._lock()
        pass
    def _lock(self):
        pass
    def _unlock(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, tp, value, traceback):
        self._unlock()
    def __del__(self):
        self._unlock()
    def fs(self):
        """
        Return the session filesystem, creating it if necessary
        """
        return HermesUserFS(self.uiSession)

class UISession(Base):
    __tablename__ = 'uisessions'
    
    sessionId = Column(String(36), primary_key=True)
    sessionDict = Column(MutableDict.as_mutable(PickleType))

    
    def __init__(self, sessionId, sessionDict):
        self.sessionId = sessionId
        self.sessionDict = sessionDict

    def __len__(self):
        return len(self.sessionDict)
    
    def __getitem__(self, key):
        return self.sessionDict[key]
    
    def __setitem__(self, key, value):
        self.sessionDict[key] = value
    
    def __delitem__(self, key):
        return self.sessionDict.__delitem__(key)
    
    def __iter__(self):
        return iter(self.sessionDict.keys())
    
    def __contains__(self, item):
        return item in self.sessionDict

    def save(self):
        SESSION.commit()

    @staticmethod
    def _getDictSummaryFromDict(dd):
        d = {}
        for k,v in list(dd.items()):
            try:
                if isinstance(v,HermesUserFS):
                    d[k] = v.getJSONSafeSummary()
                elif hasattr(v,'_toJSON'):
                    d[k] = v._toJSON()
                elif hasattr(v,'__getstate__'):
                    d[k] = v.__getstate__()
                elif isinstance(v,dict):
                    d[k] = UISession._getDictSummaryFromDict(v)
                else:
                    d[k] = v
            except Exception as e:
                d[k] = "Exception '%s' while summarizing this term" % str(e)
        return d
### Rewrote this to now be recursive   
    def getDictSummary(self):
        d = self._getDictSummaryFromDict(self.sessionDict)
        d['sessionId'] = self.sessionId
        return d
        
    def clearSessionData(self):
        with self.getLockedState() as state:
            state.fs().clearAllInfo()
        self.sessionDict = {"notes":"just cleared"}
        self.models = []

    def __str__(self):
        return "UISession('%s')>"%(self.sessionId)
        
    def __repr__(self):
        return "<UISession('%s','%s')>"%(self.sessionId,self.sessionDict)
    
    def getLockedState(self):
        return LockedState(self)

    def becomeSystem(self):
        self.sessionDict['userId'] = 1
        
    def becomeAnyone(self):
        self.sessionDict['userId'] = 2

    def getUserID(self):
        if 'userId' not in self.sessionDict:
            self.sessionDict['userId'] = 2
        return self.sessionDict['userId']
    
    def getDefaultReadGroupID(self):
        return 2
    
    def getDefaultWriteGroupID(self):
        return 2
    
    def getPrivs(self):
        """
        Returns an object bearing privilege info
        """
        return privs.Privileges(self.getUserID())

    def changed(self):
        self.sessionDict.changed()

    def getCrumbs(self):
        if 'crumbTrack' not in self.sessionDict:
            #print 'creating crumbTrack'
            self.sessionDict['crumbTrack'] = crumbtracks.StackCrumbTrail(serverconfig.rootPath,
                                                                         changeListener = self.changed)
            self.sessionDict['crumbTrack'].push(('/'+serverconfig.topPath,serverconfig.topName),
                                                argDict={'crmb':'clear'})
        crumbTrack = self.sessionDict['crumbTrack']
        if not hasattr(crumbTrack,'changeListener') or crumbTrack.changeListener is None:
            # This is always going to be true, because the changeListener will have been lost when the session was pickled
            crumbTrack.setChangeListener(self.changed)
        if 'crmb' in flask.request.params:
            if flask.request.params['crmb']=='clear':
                crumbTrack.clear()
            else:
                raise RuntimeError("The only crmb note should be 'clear'")
            del flask.request.params['crmb']
            print(flask.request.query_string)
            print([(k,v) for k,v in list(flask.request.params.items())])
#         print 'getCrumbs returning the following crumbTrack:'
#         crumbTrack._dump()
        return  crumbTrack

    @classmethod
    def getFromRequest(cls,flaskRequest):
        sessionId = flaskRequest.get_cookie("sessionId")
        defaultSessionDictContents = {"notes":"just created", "models":[], "userId":2}
        sess = SESSION
        if sessionId:
            try:
                uiSession = sess.query(UISession).filter_by(sessionId=sessionId).one()
            except NoResultFound:
                uiSession = UISession(sessionId, defaultSessionDictContents)
                sess.add(uiSession)
                sess.commit()
                # raise flask.HTTPResponse('Previous session information is not available',410)
        else:
            sessionId= "%013d_%06d_%015d"%(int(1000*time.time()),os.getpid(),_thread.get_ident())
            rootPath = flaskRequest.fullpath[:-len(flaskRequest.path)]
            flask.response.set_cookie("sessionId", sessionId, path=rootPath)
            uiSession = UISession(sessionId, defaultSessionDictContents)
            sess.add(uiSession)
            sess.commit()
#         if 'locale' in uiSession:
#             inlizer.selectLocale(uiSession['locale'])
#         else:
#             inlizer.selectLocale() # to set the default locale
        return uiSession

class UISessionPlugin(object):
    name = 'sessionsupport'
    api = 2
    def __init__(self, keyword='uiSession'):
        self.keyword = keyword
        self.sqlAlchemyKeywords = []
    def setup(self, app):
        for other in app.plugins:
            if (not isinstance(other, UISessionPlugin)
                    and not isinstance(other, flask_sqlalchemy.SQLAlchemyPlugin)):
                continue
            if isinstance(other, UISessionPlugin):
                if other.keyword == self.keyword:
                    raise flask.PluginError("Found another UISessionPlugin plugin with "
                                             "conflicting settings (non-unique keyword).")
            elif isinstance(other, flask_sqlalchemy.SQLAlchemyPlugin):
                self.sqlAlchemyKeywords.append(other.keyword)
    def apply(self, callback, route):
        # Override global configuration with route-specific values.
        conf = route.config.get('uiSession') or {}
        keyword = conf.get('keyword', self.keyword)
        # print 'conf: ', conf
        # print 'keyword: ', keyword
        
        # Test if the original callback accepts the keyword.
        # Ignore it if it does not need a handle.
        args = inspect.getargspec(route.callback)[0]
        if keyword not in args:
            return callback
        # If the callback invokes the SQLAlchemy plugin we do not need to do commits
        managedBySQLAlchemyPlugin = any([sAKwd in args for sAKwd in self.sqlAlchemyKeywords])


        def wrapper(*args, **kwargs):
            # Add the session handle as a keyword argument.
            #print '####### Applying uiSession wrapper'
            kwargs[keyword] = session = UISession.getFromRequest(flask.request)

            try:
                rv = callback(*args, **kwargs)
                if not managedBySQLAlchemyPlugin: session.save()
            except UISessionException as e:
                raise flask.FlaskException('uiSession says '+str(e))
            except flask.HTTPResponse:
                if not managedBySQLAlchemyPlugin: session.save()
                raise
            finally:
                #print "#### End uiSession plugin context"
                pass
            return rv

        # Replace the route callback with the wrapped one.
        return wrapper


def wrapFlaskApp(flaskApp, engine, Session):
    global SESSION
    SESSION = Session()
    plugin = UISessionPlugin()
    flaskApp.install(plugin)
    plugin = flask_sqlalchemy.Plugin(
        engine, # SQLAlchemy engine created with create_engine function.
        #Base.metadata, # SQLAlchemy metadata, required only if create=True.
        keyword='db', # Keyword used to inject session database in a route (default 'db').
        create=False, # If it is true, execute `metadata.create_all(engine)` when plugin is applied (default False).
        commit=True, # If it is true, plugin commit changes after route is executed (default True).
        use_kwargs=False, # If it is true and keyword is not defined, plugin uses **kwargs argument to inject session database (default False).
        create_session=Session
    )
    flaskApp.install(plugin)
    return flaskApp
