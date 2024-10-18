


# Usage


Run a validation against a given domain, and see if a) there is a CSRD report, and b) that the datapoints for a greenweb verification exist

```
carbontxt validate --greenweb-csrd domain.com
```

Run a validation against a given domain, and only say if the file is valid TOML, and it confirms to the carbon.txt spec

```
carbontxt validate --syntax-only domain
carbontxt validate --syntax-only -f ./path-to-file.com # look at the file only
```

Run a validation against a given domain, and only say if the file is valid TOML, and it confirms to the spec, AND if the links are still live

```
carbontxt validate --greenweb-csrd --syntax-only --check-links domain
```

Run a validation against a given domain, and download the evidence. Take a screenshot of the page if a webpage downloading it and the HTML, (maybe WARCing it), otherwise download the file directly otherwise.

```
carbontxt fetch --greenweb-csrd --fetch
```
