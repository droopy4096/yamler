# YAML Tools

## YAMLed

YAML stream editor. Main differencece from yq ( https://github.com/kislyuk/yq ):

1. no dependency on jq
   1. subsequently smaller scope of operations
2. does it's best to preserve order of YAML instructions ( thanks to ruamel.yaml library )
3. works only as a stream editor (i.e. you have to pipe input data in and pipe output data out)

sample.yaml:

```yaml
level1:
  sublevel1:
    subsublevel1:
      - one
      - two
  sublevel2:
    - three
    - four
```

```shell
python3 yamled.py \
    --set level2.foo:35 \
    --set level1.sublevel1.subsublevel1[2]:something \
    --merge level1.sublevel2:'["baz", "somethingelse"]' \
    --set level1.sublevel3:moo \
    < sample.yaml | tee sample_out.yaml
```

results in:

```yaml
level1:
    sublevel1:
        subsublevel1:
        - one
        - two
        - something
    sublevel2:
    - three
    - four
    - baz
    - somethingelse
    sublevel3: moo
level2:
    foo: 35
```