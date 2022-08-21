import pandas as pd
import random
import re


def mangle_1(name_dict, cands=[".", "-"], remove_space_thresh=0.4):
    cand = name_dict['midgap']
    rm_whitespace_prob = random.uniform(0, 1)
    if " " in cand and rm_whitespace_prob < remove_space_thresh:
        name_dict['midgap'] = re.sub("\s", "", cand, count=1)  # Remove only 1st whitespace

    else:
        name_dict['midgap'] = random.choice(cands) + cand
    return name_dict


def mangle_2(name_dict, front_cands=['Dr. ', 'Mr. ', 'Mrs. '],
             back_cands=[", M.D.", ", PHD", ", CFA"], remove_space_thresh=0.4):
    firstgap = name_dict['firstgap']
    lastgap = name_dict['lastgap']
    rm_whitespace_prob = random.uniform(0, 1)
    if " " in firstgap and rm_whitespace_prob < remove_space_thresh:
        name_dict['firstgap'] = re.sub("\s", "", firstgap, count=1)  # Remove only 1st whitespace

    elif " " in lastgap and rm_whitespace_prob < remove_space_thresh:
        name_dict['lastgap'] = re.sub("\s", "", lastgap, count=1)  # Remove only 1st whitespace

    else:
        # Add to either the front or back
        if random.uniform(0, 1) < 0.5:
            # Add to front
            name_dict['firstgap'] = random.choice(front_cands) + firstgap
        else:
            # Add to back
            name_dict['lastgap'] = random.choice(back_cands) + lastgap

    return name_dict


def mangle_3(name_dict):
    firstname, lastname = name_dict['firstname'], name_dict['lastname']

    # Try to get two groups from lastname (eg. McLeod -> ('Mc', "Leod"))
    try:
        grps = re.search(r"([A-Z][a-z]+)([A-Z][a-z]+)", lastname).groups()
        # If succesful, insert a hyphen
        name_dict['lastname'] = "-".join(grps)

    except:
        # Otherwise look for a vowel condition
        last_grp = re.search(r"(\w*?[^aeiou]+[aeiou])(\w+)", lastname)
        first_grp = re.search(r"(\w*?[^aeiou]+[aeiou])(\w+)", firstname)

        if last_grp is not None:
            last_grp = last_grp.groups()
            name_dict['lastname'] = "-".join(last_grp)

        elif first_grp is not None:
            first_grp = first_grp.groups()
            name_dict['firstname'] = "-".join(first_grp)

    return name_dict


def mangle_names(fullname, n_iter=5, cand_fns=[mangle_1, mangle_2, mangle_3]):
    """
    Main method for dirtying a given fullname.

    Parameters
    ----------
    fullname : str
        Given input fullname. Needs to be in form : <FirstName> <LastName> with only one whitespace in between
    n_iter : int
        Number of iterations of "mangling" to perform on a given fullname.
    cand_fns : [mangler_functions]
        List of mangler functions to choose from for each iteration

    Returns
    -------
    str :
        A mangled fullname

    """
    firstname, lastname = fullname.split(" ")
    name_dict = {
        'firstgap': "",
        'firstname': firstname,
        'midgap': " ",
        'lastname': lastname,
        'lastgap': ""
    }
    for i in range(n_iter):
        mangler_fn = random.choice(cand_fns)
        name_dict = mangler_fn(name_dict)

    return "".join(name_dict.values())