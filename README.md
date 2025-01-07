# python-qobuz

Unofficial python library for the [Qobuz-API  (project removed)](https://github.com/Qobuz/api-documentation).<br>
Cloned and updated from [python-qobuz](https://github.com/taschenb/python-qobuz)

## Installation

* download code from zip, unzip in "ANYWHERE" and run "``pip install "ANYWHERE"/qobuz``"

or

* run "``pip install git+https://github.com/fdenivac/python-qobuz``"



## Usage
In order to use the library, your application needs a valid APP_ID.
For streaming audio, you also need a valid APP_SECRET.
Both id and secret can be requested from [api@qobuz.com](mailto:api@qobuz.com).<br>

```python
import qobuz

# Register your APP_ID
qobuz.register_app("YOUR_APP_ID")

# Or register your APP_ID and APP_SECRET
qobuz.register_app("YOUR_APP_ID", "YOUR_APP_SECRET")
```


For a complete usage, see project [myqobuz](https://github.com/fdenivac/myqobuz)