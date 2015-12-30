#Umpire

Umpire is a generic dependency resolver which aims to be both platform agnostic, and downright simple to use. It is developed in Python and is easily extensible.

Using an S3 backed repository of compressed packages, Umpire reads a simple JSON file to retrieve, cache, and link files to their appropriate destination. It's original use case was to keep binary artifacts and tools out of git repositories, but still provide a way for these binaries to be versioned.

Umpire is being developed as an easy to install command line tool, with it's flexibility being derived from the JSON file options.

### Version History

**v0.2.0**

 Initial working version of Umpire
  - Dependencies will automatically link to their destination
  - Dependencies will automatically unpack when added to the cache
  - Dependencies will automatically download when missing from the cache

### Installation
Installing Umpire is easy. All you need is the pip package manager, and Python version 2.7.x (Windows **requires** version **2.7.11**).

```
$ pip install umpire
```

Don't have pip? Get it [here.](https://pypi.python.org/pypi/pip)

### Examples

Below is an example deployment JSON file, taken from one of our projects at Signiant. The URL is composed of the identifier (s3://) and the bucket name, which as of version 0.2.0 should be anonymously accessible.

The items array contains the list of dependencies. Each one requires a platform, name and version. In the s3 bucket they need to be stored with the prefix: **$PLATFORM/$NAME/$VERSION**. Umpire does a case insensitive match against this naming convention to find the appropriate dependency. It will download all files matching the prefix in the bucket, and will attempt to unpack them for future deployment.
```
[
  {
    "url":"s3://thirdpartydependencies/",
    "items":[
	      {
	        "name":"zlib",
	        "version":"1.2.8",
	        "platform":"win64",
	        "destination":"./destination/zlib/"
	      },
	      {
		    "name":"swigwin",
		    "version":"3.0.2",
		    "platform":"win64",
		    "destination":"./destination/swigwin/"
	      }
	    ]
   }
]
```

### Development

Want to help out? Awesome!

We'll gladly take any help in bug fixes, or feature updates if it fits within our whole vision of Umpire. Feel free to create a fork of the repository, and submit a pull request if you do anything cool.

##### Todos

 - MD5 verification support
 - Publishing support
 - Authenticated S3 access
 - Zip, Bzip support
 - Optional unpacking
 - Multi-package bucket support
 - File exclusion (regex)

License
----

Umpire is licensed under the [MIT license](https://github.com/Signiant/umpire/blob/develop/LICENSE)
