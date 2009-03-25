/**
 *  Prototype Xtensions 
 *  
 *  @author  Simon Martins
 *  @copyright (c) 2008 Netatoo SARL <http://www.netatoo.fr>
 *  @license   MIT License <http://www.prototypextensions.com/#main=license>
 * 
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 *  THE SOFTWARE.
 *
 */
 
/**
 * Prototype.X requirements
 */
Prototype.X = {};

/**
 * Prototype.X.Browser
 *
 * @desc Used to retrieve the browser version
 */
(function() {
  var nav     = navigator;
  var userAgent = ua = navigator.userAgent;
  var v     = nav.appVersion;
  var version   = parseFloat(v);

  Prototype.X.Browser = {
    IE    : (Prototype.Browser.IE)  ? parseFloat(v.split("MSIE ")[1]) || 0 : 0,
    Firefox : (Prototype.Browser.Gecko) ? parseFloat(ua.split("Firefox/")[1]) || 0 : 0,
    Camino  : (Prototype.Browser.Gecko) ? parseFloat(ua.split("Camino/")[1]) || 0 : 0,
    Flock   : (Prototype.Browser.Gecko) ? parseFloat(ua.split("Flock/")[1]) || 0 : 0,
    Opera   : (Prototype.Browser.Opera) ? version : 0,
    AIR   : (ua.indexOf("AdobeAIR") >= 0) ? 1 : 0,
    Mozilla : (Prototype.Browser.Gecko || !this.Khtml) ? version : 0,
    Khtml   : (v.indexOf("Konqueror") >= 0 && this.safari) ? version : 0,
    Safari  : (function() {
      var safari = Math.max(v.indexOf("WebKit"), v.indexOf("Safari"), 0);
      return (safari) ? (
        parseFloat(v.split("Version/")[1]) || ( ( parseFloat(v.substr(safari+7)) >= 419.3 ) ? 3 : 2 ) || 2
      ) : 0;
    })()
  };
})();

// -------------------------------------------------------------------

/**
 * History
 *
 * @desc Provides basic methods to manage the history browsing.
 */
var History = {
  __altered: false,
  __currentHash: null,
  __previousHash: null,
  __iframe: false,
  __title: false,
  
  /**
   * init()
   * @desc Initialize the hash. Call this method in first
   */
  init: function() {
    var inst  = this;
    var hash  = location.hash.substring(1);
    this.hash = $H(hash.toQueryParams());
    this.__currentHash  = hash;
    this.__previousHash = hash;

    this.__title = document.title;
    
    if(Prototype.Browser.IE && Prototype.X.Browser.IE < 8) {
      document.observe('dom:loaded', function(e) {
        if(!$('px-historyframe')) {
          History.__iframe = new Element('iframe', {
            name   : 'px-historyframe',
            id   : 'px-historyframe',
            src  : '',
            width  : '0',
            height : '0',
            style  : {
              visibility: 'hidden'
            }
          });
          
          document.body.appendChild(History.__iframe);
          
          History.setHashOnIframe(inst.hash.toQueryString());
        }
      });
    }
  },
  
  /**
   * set( string $name, string $value )
   *
   * @desc Set new value $value for parameter $name
   */
  set: function($name, $value) {
    var obj = {};
    obj[$name] = $value;
    this.setMultiple(obj);
  },
  
  setMultiple: function($obj) {
    this.__previousHash = this.hash.toQueryString();
    for (var p in $obj) {
      if ($obj[p] == null) {
        this.hash.unset(p);
      } else {
        this.hash.set(p, $obj[p]);
      }
    }
    this.apply();
  },
  
  /**
   * get( string $name )
   *
   * @desc Get value parameter $name
   */
  get: function($name) {
    return this.hash.get($name);
  },
  
  /**
   * unset( string $name )
   *
   * @desc Unset parameter $name
   */
  unset: function($name) {
    this.hash.unset($name);
    this.apply();
  },
  
  /**
   * update()
   *
   * @desc Updates this.hash with the current hash
   */
  update: function() {
    this.__previousHash = this.hash.toQueryString();
    var hash = window.location.hash.substring(1);

    // If IE, look in the iframe to see if if the hash is updated
    if(Prototype.Browser.IE && Prototype.X.Browser.IE < 8 && this.__iframe ) {
      var hashInFrame = this.getHashOnIframe();
      
      if(hashInFrame != hash) {
        hash = hashInFrame;
        // window.location.hash should be updated to match
        window.location.hash = hash;
      }
    }

    this.hash = $H(hash.toQueryParams());
    this.__currentHash = hash;
  },
  
  /**
   * apply()
   *
   * @desc Apply this.hash to location.hash
   */
  apply: function() {
    var newHash = this.hash.toQueryString();

    // set new hash
    window.location.hash = newHash.length > 0 ? newHash : "#";
    
    // If IE, apply new hash to frame for history  
    if(Prototype.Browser.IE && Prototype.X.Browser.IE < 8 && this.__iframe) {
      if(this.__currentHash != newHash || newHash != this.getHashOnIframe()) 
      {
        this.setHashOnIframe(newHash);
      }
    }
  },

  /**
   * isAltered()
   *
   * @desc Return true if current hash is different of previous hash.
   * this.__altered allows to force the dispatch.
   */
  isAltered: function() {
    if(this.__altered == true) {
      return true;
    }
    this.__altered = false;

    return (History.__currentHash != History.__previousHash);
  },
  
  /**
   * setHashOnIframe()
   *
   * @use  For IE compatibility
   * @desc Set hash value on iframe
   */
  setHashOnIframe: function(hash) {
    try {
      var doc = History.__iframe.contentWindow.document;
      doc.open();
      doc.write('<html><body id="history">' + hash + '</body></html>');
      doc.close();
    } catch(e) {}
  },
  
  /**
   * getHashOnIframe()
   *
   * @use  For IE compatibility
   * @desc Get hash value on iframe
   */
  getHashOnIframe: function() {
    var doc = this.__iframe.contentWindow.document;
    if (doc && doc.body.id == 'history') {
      return doc.body.innerText;
    } else {
      return this.hash.toQueryString();
    }
  },
  
  /**
   * setTitle()
   *
   * @desc Set a new title for window
   */
  setTitle: function(title) {
    if(document.title) {
      document.title = title;
    }
  },
  
  /**
   * getTitle()
   *
   * @desc Return current window title
   */
  getTitle: function() {
    return this.__title;
  }
};
History.init();

/**
 * History.Observer
 *
 * @desc Used to perform actions defined in the registry, 
 * according to the hash of the url.
 */
History.Observer = {
  delay : 0.2,
  executer : null,
  started : false,
  
  start: function() {
    if(this.started) return;
    this.executer = new PeriodicalExecuter(History.Observer.dispatch.bind(this), this.delay);
    this.started = true;
  },
  
  stop: function() {
    if(!this.started) return;
    this.executer.stop();
    this.started = false;
  },

  observers: function(key) {
    if (!this.__observers) {
      this.__observers = {};
    }
    if (typeof key == 'undefined')
    {
      return this.__observers;
    }
    return this.__observers[key] || [];
  },
  
  observe: function(key, callback) {
    var observers = this.observers();
    if (!observers[key]) {
      observers[key] = [];
    }
    observers[key].push(callback);
  },
  
  dispatch: function() {
    // Update the hash
    History.update();
      
    // Dispatch only if location.hash has been altered
    if(History.isAltered()) {
      this.observers('all').each(function(observer){
        observer('all',null);
      });
      
      //if(console) console.log('pass');
      History.hash.each(function(pair) {
        this.observers(pair.key).each(function(observer){
          observer(pair.key,pair.value);
        });
      },this);
    }
  }
};
