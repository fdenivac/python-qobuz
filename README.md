# python-qobuz

Unofficial python library for the [Qobuz-API (project removed)](https://github.com/Qobuz/api-documentation).<br>
Cloned and updated from [python-qobuz](https://github.com/taschenb/python-qobuz)

## Installation

* download code from zip, unzip in "ANYWHERE" and run "``pip install "ANYWHERE"/qobuz``"

or

* run "``pip install git+https://github.com/fdenivac/python-qobuz``"



## Usage
In order to use the library, your application needs to be authenticated via OAuth.<br>
On first use, or when authentication expires, call something as :
```python
from qobuz.qoauth import QobuzOAuth

from MyConfig import qobuz_config

myconfig = qobuz_config.get_config()
if QobuzOAuth().handle_oauth_login():
    myconfig["user_id"] = auth.oauth_user_id
    myconfig["auth_token"] = auth.oauth_user_auth_token
    myconfig["app_id"] = auth.app_id
    myconfig["secrets"] = ",".join(auth.secrets)
    myconfig["private_key"] = auth.private_key
    qobuz_config.write()
```
... and follow authenticate instructions.
<br>
<br>
You can now use library as :
```python
import qobuz
from qobuz.qopy import qobuz_api
from MyConfig import qobuz_config

myconfig = qobuz_config.get_config()
qobuz_api.connect_with_token(
    myconfig["user_id"],
    myconfig["auth_token"],
    myconfig["app_id"],
    myconfig["secrets"].split(","),
    )

albums = qobuz.Album.search("relaxing")
...
```


For a complete usage, see project [myqobuz : python script managing playlists and favorites](https://github.com/fdenivac/myqobuz)