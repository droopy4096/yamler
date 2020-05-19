#!/bin/env python

import sys
import ruamel.yaml as ryaml
import argparse
import scalpl
import json
import logging

log=logging.getLogger(__name__)

# import addict
# import jmespath

def join_path(path):
    if len(path)<1:
        return ""

    if isinstance(path[0],int):
        res="[{0}]".format(path[0])
    else:
        res=path[0]
    for i, key in enumerate(path[1:]):
        if isinstance(key,int):
            res=res+"[{0}]".format(key)
        else:
            res=res+"."+key
    return res


class NoChild(Exception):
    def __init__(self, parent, child_path, parent_path):
        self.parent=parent
        self.child_path=child_path
        self.parent_path=parent_path

def render_expression(expression):
    raw_path, raw_value = expression.split(':',1)
    path=scalpl.scalpl.split_path(raw_path,'.')
    str_value=raw_value.lstrip().rstrip()
    try:
        value=json.loads(str_value)
    except:
        value=str_value
    
    return {'path':path, 'jmespath': raw_path, 'value': value}


def safe_set(data, keys, new_value):
    log.debug("In\n\t{0}\n\tsetting the keys:{1}\n\twith new value:{2}".format(str(data),str(keys),str(new_value)))
    value = data
    i = 0
    key = None
    if len(keys)<1:
        return data
    try:
        for i, key in enumerate(keys[:-1]):
            value = value[key]
        value[keys[-1]]=new_value
    except KeyError as error:
        log.debug("Exception: K val:{0} key:{1} keys:{2}".format(str(value), str(key), str(keys)) )
        raise NoChild(value, keys[i+1:], keys[:i+1])
    except IndexError as error:
        log.debug("Exception: I val:{0} key:{1} keys:{2}".format(str(value), str(key), str(keys)) )
        raise NoChild(value, keys[i+1:], keys[:i+1])
    except TypeError:
        log.debug("Exception: T val:{0} key:{1} keys:{2}".format(str(value), str(key), str(keys)) )
        raise NoChild(value, keys[i+1:], keys[:i+1])
    return value

def safe_merge(data, keys, new_value):
    log.debug("In\n\t{0}\n\tsetting the keys:{1}\n\twith new value:{2}".format(str(data),str(keys),str(new_value)))
    value = data
    i = 0
    key = None
    if len(keys)<1:
        return data
    try:
        for i, key in enumerate(keys[:-1]):
            value = value[key]
        cur_val=value[keys[-1]]
        if isinstance(cur_val, list) and isinstance(new_value,list):
            value[keys[-1]].extend(new_value)
        elif isinstance(cur_val, dict) and isinstance(new_value,dict):
            value[keys[-1]].update(new_value)
        else:
            value[keys[-1]]=new_value
    except KeyError as error:
        log.debug("Exception: K val:{0} key:{1} keys:{2}".format(str(value), str(key), str(keys)) )
        raise NoChild(value, keys[i+1:], keys[:i+1])
    except IndexError as error:
        log.debug("Exception: I val:{0} key:{1} keys:{2}".format(str(value), str(key), str(keys)) )
        raise NoChild(value, keys[i+1:], keys[:i+1])
    except TypeError:
        log.debug("Exception: T val:{0} key:{1} keys:{2}".format(str(value), str(key), str(keys)) )
        raise NoChild(value, keys[i+1:], keys[:i+1])
    return value

def create_leaf(data, setter):
    try:
        leaf=safe_set(data, setter["path"], setter["value"])
    except NoChild as error:
        parent=error.parent
        parent_path=error.parent_path
        child_path=error.child_path
        log.debug("No Child for \n\tparent:{0}\n\tat path:{1}\n\tcan't establish child path:{2}".format(str(parent),str(parent_path),str(child_path)))
        # create child branch:
        child_branch={}
        child_branch_key=parent_path[-1]
        child=child_branch
        for depth, key in enumerate(child_path[1:]):
            if depth<len(child_path)-2:
                child[key]={}
                child=child[key]
            else:
                child[key]=setter['value']
        log.debug("Generated Child branch: {0}".format(str(child_branch)))
        if isinstance(parent, list):
            # we don't seem to reach this block
            log.debug("Parent is a list: parent:{0} parent_path:{1} child_path:{2}".format(str(parent), str(parent_path), str(child_path)))
            dict_replacement={ i: elem for i,elem in enumerate(parent) }
            log.debug("Replacement dict: {0}".format(str(dict_replacement)))
            safe_set(data, parent_path, dict_replacement)
            log.debug("Found list, converted to dict: {0}".format(str(dict_replacement)))
            processor=scalpl.Cut(data)
            log.debug("New state: {0}".format(str(processor[join_path(parent_path)])))
            # processor.update({ join_path(parent_path+[child_branch_key]): child_branch})
        elif isinstance(parent, dict):
            ## why would that even trigger
            log.debug("Parent is a dict: parent:{0} parent_path:{1} child_path:{2}".format(str(parent), str(parent_path), str(child_path)))
            # raise Exception("Unknown exception")
            pass
        else:
            log.debug("Parent a scalar: parent:{0} parent_path:{1} child_path:{2}".format(str(parent), str(parent_path), str(child_path)))
            safe_set(data, parent_path, {})
        log.debug("Before safe_set: {0}".format(str(data)))
        safe_set(data, parent_path+[child_branch_key], child_branch)
        log.debug("After safe_set: {0}".format(str(data)))
        # processor=scalpl.Cut(parent)
        # processor.update(child_branch)

def create_leaf(data, setter):
    try:
        leaf=safe_set(data, setter["path"], setter["value"])
    except NoChild as error:
        parent=error.parent
        parent_path=error.parent_path
        child_path=error.child_path
        log.debug("No Child for \n\tparent:{0}\n\tat path:{1}\n\tcan't establish child path:{2}".format(str(parent),str(parent_path),str(child_path)))
        child_branch={}
        child_branch_key=child_path[0]
        child=child_branch
        for depth, key in enumerate(child_path):
            if depth<len(child_path)-1:
                child[key]={}
                child=child[key]
            else:
                child[key]=setter['value']
        log.debug("Generated Child branch: {0}".format(str(child_branch)))
        if isinstance(parent, list):
            log.debug("Parent is a list: parent:{0} parent_path:{1} child_path:{2}".format(str(parent), str(parent_path), str(child_path)))
            if isinstance(child_branch_key, int):
                parent.append(child_branch[child_branch_key])
        elif isinstance(parent, dict):
            log.debug("Parent is a dict: parent:{0} parent_path:{1} child_path:{2}".format(str(parent), str(parent_path), str(child_path)))
            # raise Exception("Unknown exception")
            log.debug("Scalped parent: {0}".format(str(parent)))
            safe_set(data, parent_path, child_branch)
        else:
            safe_set(data, parent_path, {})
            safe_set(data, parent_path, child_branch)

def update_leaf(data, setter):
    try:
        leaf=safe_merge(data, setter["path"], setter["value"])
    except NoChild as error:
        parent=error.parent
        parent_path=error.parent_path
        child_path=error.child_path
        log.debug("No Child for \n\tparent:{0}\n\tat path:{1}\n\tcan't establish child path:{2}".format(str(parent),str(parent_path),str(child_path)))
        # new_dict=addict.Dict()
        # create child branch:
        child_branch={}
        child_branch_key=child_path[0]
        child=child_branch
        for depth, key in enumerate(child_path):
            if depth<len(child_path)-1:
                child[key]={}
                child=child[key]
            else:
                child[key]=setter['value']
        log.debug("Generated Child branch: {0}".format(str(child_branch)))
        if isinstance(parent, list):
            log.debug("Parent is a list: parent:{0} parent_path:{1} child_path:{2}".format(str(parent), str(parent_path), str(child_path)))
            if isinstance(child_branch_key, int):
                parent.append(child_branch[child_branch_key])
            ### dict_replacement={ i: elem for i,elem in enumerate(parent) }
            ### safe_set(data, parent_path, dict_replacement)
            ### print("Found list, converted to dict: {0}".format(str(dict_replacement)))
            ### processor=scalpl.Cut(data)
            ### print("New state: {0}".format(str(processor[join_path(parent_path)])))
            ### # processor.update({ join_path(parent_path+[child_branch_key]): child_branch})
        elif isinstance(parent, dict):
            ## why would that even trigger
            log.debug("Parent is a dict: parent:{0} parent_path:{1} child_path:{2}".format(str(parent), str(parent_path), str(child_path)))
            # raise Exception("Unknown exception")
            processor=scalpl.Cut(parent)
            log.debug("Scalped parent: {0}".format(str(processor)))
            processor.update({ parent_path[-1]: child_branch})
        else:
            log.debug("Or else...")
            safe_set(data, parent_path, {})
            safe_set(data, parent_path, child_branch)

        ### print("Before safe_set: {0}".format(str(data)))
        ### safe_set(data, parent_path, child_branch)
        ### print("After safe_set: {0}".format(str(data)))
        # processor=scalpl.Cut(parent)
        # processor.update(child_branch)

def process_data(data, setters, mergers):
    processor=scalpl.Cut(data)
    for setter in setters:
        try:
            del processor[setter['jmespath']]
        except (KeyError, IndexError) as error:
            # it's not there anyway
            pass
        try:
            processor.update({setter['jmespath']: setter['value']})
        except (KeyError, IndexError) :
            create_leaf(data, setter)

    for merger in mergers:
        try:
            update_leaf(data, merger)
            # processor.update({merger['jmespath']: merger['value']})
        except (KeyError, IndexError):
            # update_leaf(data, merger)
            pass

    
if __name__ == "__main__":
    # log.basicConfig(level=log.INFO)
    parser = argparse.ArgumentParser(description='YAML stream editor')
    parser.add_argument('--merge', dest='mergers', action='append', default=[],
                        help='merge expressions')
    parser.add_argument('--set', dest='setters', action='append', default=[],
                        help='set expressions')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False,
                        help='Enable debug info')

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(levelname)s %(lineno)s - %(message)s')
        ch.setFormatter(formatter)
        log.addHandler(ch)


    mergers=[]

    for merge_arg in args.mergers:
        merge=render_expression(merge_arg)
        mergers.append(merge)

    setters=[]
    for set_arg in args.setters:
        setter=render_expression(set_arg)
        setters.append(setter)

    yaml=ryaml.YAML()
    yaml.indent(mapping=4)
    data=yaml.load(sys.stdin)
    # now, process
    process_data(data,setters,mergers)
    yaml.dump(data,sys.stdout)