from time import time
import numpy as np
import pandas as pd
import itertools
from itertools import product
from pandas.api.types import is_numeric_dtype, is_datetime64_any_dtype, is_categorical_dtype

class Stainer:
    """Parent Stainer class that contains basic initialisations meant for all stainers to inherit from.

    Note
    ----
    This class is not meant to be used on its own, and is meant as the superclass of any custom stainer that may be developed in the future.

    Attributes
    ----------
    name : str
        Name of stainer.
    row_idx : int list
        Row indices that the stainer will operate on.
    col_idx : int list
        Column indices that the stainer will operate on.
    col_type : str
        Column type that the stainer operates on, used for stainer to automatically select viable columns to operate on, if the user does not
        pass in any col_idx. Currently supports ["all", "category", "cat", "datetime", "date", "time", "numeric", "int", "float"].
    """
    #: Defaults to "all", indicating all columns will be selected
    col_type = "all"
    
    def __init__(self, name = "Unnamed Stainer", row_idx = [], col_idx = []):
        """The constructor for Stainer class.  
        
        Parameters
        ----------
        name : str, optional
            Name of stainer. Default is "Unnamed Stainer".
        row_idx : int list, optional
            Row indices that the stainer will operate on. Default is empty list.
        col_idx : int list, optional
            Column indices that the stainer will operate on. Default is empty list.
        """
        self.name = name
        self.row_idx = row_idx
        self.col_idx = col_idx
        
        self.__initialize_history__()

    def get_col_type(self):
        """Returns the column type that the stainer operates on.
        
        Returns
        -------
        string
            Column type that the stainer operates on.
        """
        return self.col_type

    def get_indices(self):
        """Returns the row indices and column indices.

        Returns
        -------
        row_idx : int list
            Row indices that the stainer operates on.
        col_idx : int list
            Column indices that the stainer operates on.
        """
        return self.row_idx, self.col_idx
    
    def transform(self, df, rng, row_idx, col_idx):
        """Applies staining on the given indices in the provided dataframe.
        
        Note
        ----
        This method does not return anything and simply raises an error. However, it is expected for the user to implement the transform method 
        for their custom user-defined stainers.

        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list
            Row indices that the stainer will operate on. Will take priority over the class attribute `row_idx`.
        col_idx : int list
            Column indices that the stainer will operate on. Will take priority over the class attribute `col_idx`.
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : {int: int} dictionary 
            Row mapping showing the relationship between the original and new row positions.
        col_map : {int: int} dictionary 
            Column mapping showing the relationship between the original and new column positions.
        
        Raises
        ------
        Exception
            Children class does not implement the transform method.
        """
        raise Exception("Stainer not implemented")

    def _init_transform(self, df, row_idx, col_idx):
        """Helper method to assign df, row_idx, and col_idx at the start of the self.transform() method.
        
        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        row_idx : int list
            Row indices that the stainer will operate on. Will take priority over the class attribute `row_idx`.
        col_idx : int list
            Column indices that the stainer will operate on. Will take priority over the class attribute `col_idx`.
        
        Returns
        -------
        new_df : pd.DataFrame 
            A copy of the input Dataframe.
        row_idx : int list
            Processed list of row indices which will be selected for transformation.
        col_idx : int list
            Processed list of column indices which will be selected for transformation.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError('df should be pandas DataFrame')
        
        new_df = df.copy()
        
        if not row_idx:
            row_idx = self.row_idx
        if not col_idx:
            col_idx = self.col_idx

        return new_df, row_idx, col_idx
                           
    # History-related methods #
    def __initialize_history__(self):
        self.message = ""
        self.time = 0
    
    def update_history(self, message = "", time = 0):
        """Used by transform method to set attributes required to display history information
        
        Parameters
        ----------
        message : str
            Mesasge to be shown to user about the transformation
        time: float
            Time taken to perform the transform
        """
        self.message += message
        self.time += time
    
    def get_history(self):
        """Compiles history information for this stainer and returns it.
        
        Returns
        -------
        name : str
            Name of stainer.
        msg : str
            Message for user.
        time : float
            Time taken to execute the self.transform() method.
        """
        msg, time = self.message, self.time
        if not time:
            time = "Time not updated. Use update_history to update time"
        self.__initialize_history__()
        return self.name, msg, time
    
    
class ShuffleStainer(Stainer):
    """ Stainer to randomly rearrange the rows of the DataFrame """
    
    def __init__(self, name = "Shuffle"):   
        """ Constructor for ShuffleStainer
        
        Parameters
        ----------
        name : str, optional
            Name of stainer. Default is "Shuffle"
        """
        super().__init__(name, [], [])
        
    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.
        
        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter. All rows will be shuffled regardless
        col_idx : int list, optional
            Unused parameter. All columns will be shuffled regardless
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            Row mapping showing the relationship between the original and new row positions.
        col_map : empty dictionary
            This stainer does not produce any column mappings.
        """
        new_df, row_idx, col_idx = self._init_transform(df, row_idx, col_idx)

        start = time()
        # Shuffle + Create mapping
        new_df["_extra_index_for_stainer"] = range(df.shape[0])
        new_df = new_df.sample(frac = 1, random_state = rng.bit_generator)
        new_idx = new_df["_extra_index_for_stainer"].tolist()
        new_df.drop("_extra_index_for_stainer", axis = 1, inplace = True)
        new_df.reset_index(inplace = True, drop = True)
        
        row_map = {}
        for i in range(df.shape[0]):
            row_map[new_idx[i]] = [i]

        end = time()
        self.update_history("Order of rows randomized", end - start)
        return new_df, row_map, {}      
    
    
class RowDuplicateStainer(Stainer):
    """ Stainer to duplicate rows of a dataset. """  
    def __init__(self, deg, max_rep = 2, name = "Add Duplicates", row_idx = []):
        """ Constructor for RowDuplicateStainer 
        
        Parameters
        ----------
        deg : float (0, 1]
            Proportion of given data that would be duplicated.
            Note: If 5 rows were specified and deg = 0.6, only 3 rows will be duplicated
        max_rep : (2/3/4/5), optional
            Maximum number of times a row can appear after duplication. That is, if max_rep = 2, 
            the original row was duplicated once to create 2 copies total.
            Capped at 5 to conserve computational power.
            Defaults to 2
        name : str, optional
            Name of stainer. Default is "Add Duplicates"
        row_idx : int list, optional
            Row indices that the stainer will operate on. Default is empty list.
            
        Raises
        ----------
        ValueError
            Degree provided is not in the range of (0, 1]
        ValueError
            max_rep is not in the range of [2, 5]
        """
        super().__init__(name, row_idx, [])
        if deg <= 0 or deg > 1:
            raise ValueError("Degree should be in range (0, 1]")
        self.deg = deg
        if max_rep not in [2, 3, 4, 5]:
            raise ValueError("max_rep should be in range [2, 5]")
        self.max_rep = max_rep

    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.
        
        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Row indices that the stainer will operate on. Default is empty list.
        col_idx : int list, optional
            Unused parameter. Columns will be duplicated when new rows are created.
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            Row mapping showing the relationship between the original and new row positions.
        col_map : empty dictionary
            This stainer does not produce any column mappings. 
        """
        _, row, col = self._init_transform(df, row_idx, col_idx)
        original_types = df.dtypes
        new_df = []
        row_map = {} 
        
        start = time()
        idx_to_dup = rng.choice(row, size = int(self.deg * df.shape[0]), replace = False)
        idx_to_dup.sort()
        
        new_idx = 0
        for old_idx, *row in df.itertuples():
            row_map[old_idx] = []
            if len(idx_to_dup) and old_idx == idx_to_dup[0]:
                num_dup = rng.integers(2, self.max_rep, endpoint = True)
                new_df.extend([list(row)] * num_dup)
                for i in range(num_dup):
                    row_map[old_idx].append(new_idx)
                    new_idx += 1
                idx_to_dup = idx_to_dup[1:]
            else:
                new_df.append(list(row))
                row_map[old_idx].append(new_idx)
                new_idx += 1
        
        new_df = pd.DataFrame(new_df, columns = df.columns)
        
        for i in range(new_df.shape[1]): # Assign back original column types
            new_df.iloc[:, i] = new_df.iloc[:, i].astype(original_types[i])
            
        end = time()
        
        message = f"Added Duplicate Rows for {int(self.deg * df.shape[0])} rows. \n" + \
                  f"  Each duplicated row should appear a maximum of {self.max_rep} times. \n" + \
                  f"  Rows added: {new_df.shape[0] - df.shape[0]}"
        
        self.update_history(message, end - start)
        
        return new_df, row_map, {}
    
class InflectionStainer(Stainer):
    """Stainer to introduce random string inflections (e.g. capitalization, case format, pluralization) to given categorical columns.
    """
    #: Set as "cat" - only categorical columns will be selected for inflection
    col_type = 'cat'

    def __init__(self, col_idx = [], name = "Inflection", ignore_cats = [], num_format = -1, formats = None):
        """The constructor for InflectionStainer class.  
        
        Parameters
        ----------
        name : str, optional
            Name of stainer. Default is "Inflection".
        col_idx : int list, optional
            Column indices that the stainer will operate on. Default is empty list.
        ignore_cats : str list or {int: str list}, optional
            Category strings to be ignored by stainer. If input is string list: for all columns, ignore all categories present within the list.
            If inut is dict: maps each col_idx to list of ignored category strings for that particular column. Default is empty list.
        num_format : int, optional
            Number of inflection formats present within each column. If num_format > number of available formats, 
            or num_format == -1, use all formats. Default is -1.
        formats : str list or None, optional
            List of inflection format options to chooses from. Choose from the following options: {'original', 'uppercase', 'lowercase', 
            'capitalize', 'camelize', 'pluralize', 'singularize', 'dasherize', 'humanize', 'titleize', 'underscore'}. 
            If None, all inflections are used.
        """
        super().__init__(name, [], col_idx)
        self.num_format = num_format
        
        
        if isinstance(ignore_cats, list): # convert from list to dict
            temp_ignore_cats = ignore_cats.copy()
            self.ignore_cats = {j: temp_ignore_cats for j in col_idx}
        elif isinstance(ignore_cats, dict):
            self.ignore_cats = ignore_cats
        else:
            raise TypeError("ignore_cats must be either a list of strings, or a dictionary mapping column index to list of strings")

        if formats:
            self.formats = formats
        else:
            self.formats = ['original', 'uppercase', 'lowercase', 'capitalize', 'camelize', 'pluralize', 'singularize', 'dasherize', 'humanize',
                'titleize', 'underscore'] #default formats; 10 total inflections + original

    def _get_inflected_strings(self, x, formats):
        """Internal helper to get inflected strings.

        Parameters
        ----------
            x : str
                A category string.
            formats : str list
                A list of string formats.
                
        Returns
        -------
        str set
            a set of strings, one for each inflection format in formats.
        """
        import inflection

        default_format_map = {
            'original': lambda x: x,
            'uppercase': lambda x: x.upper(), 
            'lowercase': lambda x: x.lower(), 
            'capitalize': lambda x: x.capitalize(), 
            'camelize': inflection.camelize, 
            'pluralize': inflection.pluralize, 
            'singularize': inflection.singularize,
            'dasherize': inflection.dasherize, 
            'humanize': inflection.humanize, 
            'titleize': inflection.titleize, 
            'underscore': inflection.underscore}

        output_set = set()
        for format in formats:
            output_set.add(default_format_map[format](x))
        return output_set
        
    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.

        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter as this stainer does not use row indices.
        col_idx : int list, optional
            Column indices that the stainer will operate on. Will take priority over the class attribute `col_idx`.
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : empty dictionary
            This stainer does not produce any column mappings.
        """
        new_df, row_idx, col_idx = self._init_transform(df, row_idx, col_idx)

        start = time()

        message = "Categorical inflections on:\n"
        inflections_used = dict() #dict of dicts to store inflections used for history

        #iterate over each column index
        for j in col_idx:
            new_col = df.iloc[:, j].copy() #instantiate a copy of this column which will be used to replace the existing one in new_df
            inflections_used[j] = dict()
            cats = [cat for cat in new_col.unique()] #unique categories in the column
            if self.num_format == -1 or self.num_format > len(self.formats):
                subformats = self.formats #use all formats
            else:
                subformats = rng.choice(self.formats, size=self.num_format, replace=False) #randomly select num_format formats from self.formats to be used for this column
            
            new_col_lst = []
            #interate over each string category
            for cat in cats:
                if pd.isnull(cat):
                    continue
                sub_col = new_col[new_col == cat] #subset of col which only contains this category

                if j in self.ignore_cats.keys() and cat in self.ignore_cats[j]: #ignore this category
                    new_col_lst.append(sub_col)
                else:
                    cat_inflection_formats = self._get_inflected_strings(cat, subformats) #set of inflected strings for this category
                    
                    inflections_used[j][cat] = list(cat_inflection_formats)

                    new_col_lst.append(
                        pd.Series(rng.choice(list(cat_inflection_formats), size = sub_col.shape[0]), index=sub_col.index)
                    ) #randomly sample the strings from the available inflections    
            new_col = pd.concat(new_col_lst).reindex(new_col.index) #reindex based on original df index.
            new_df.iloc[:, j] = new_col
        
        end = time()
        message += {new_df.columns[k]: v for k, v in inflections_used.items()}.__repr__()
        self.update_history(message, end - start)
        return new_df, {}, {}

class DatetimeFormatStainer(Stainer):
    """Stainer to alter the format of datetimes for given datetime columns.
    """
    #: Set as "datetime" - only datetime/date/time columns will be selected for formatting
    col_type = "datetime"

    def __init__(self, name = "Datetime Formats", col_idx = [], num_format = 2, formats = None):
        """The constructor for DatetimeFormatStainer class.  
        
        Parameters
        ----------
        name : str, optional
            Name of stainer. Default is "Datetime Formats".
        col_idx : int list, optional
            Column indices that the stainer will operate on. Default is empty list.
        num_format : int, optional
            Number of datetime formats present within each column. If num_format > number of available formats, 
            or num_format == -1, use all formats. Default is 2.
        formats : str list or None, optional
            List of datetime string format options that the DatetimeFormatStainer chooses from. Use datetime module string formats (e.g. '%d%b%Y'). 
            If None, a default list of 41 non-ambiguous (month is named) datetime formats are provided. Default is None.
        """
        import itertools
        
        super().__init__(name, [], col_idx)
        self.num_format = num_format

        if formats:
            self.formats = formats
        else:
            self.formats = [date + " %H:%M:%S" for date in [f"{dm_y[0]}{br}{dm_y[1]}" for br in [",", ", ", "-", "/", " "]
                                for m_type in ["%b", "%B"]
                                for d_m in itertools.permutations(["%d", m_type])
                                for d_m_str in [f"{d_m[0]}{br}{d_m[1]}"]
                                for dm_y in itertools.permutations([d_m_str, '%Y'])
                           ] + ['%Y%m%d']] #default formats; 41 total and non-ambiguous
            
        
    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.

        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter as this stainer does not use row indices.
        col_idx : int list, optional
            Column indices that the stainer will operate on. Will take priority over the class attribute `col_idx`.
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : empty dictionary
            This stainer does not produce any column mappings.
        """
        new_df, row_idx, col_idx = self._init_transform(df, row_idx, col_idx)

        start = time()
        nrow = new_df.shape[0]
        message = "Date Formats used:\n"
        date_formats_used = {} #dict to store date formats used
        
        #iterate over each column index
        for j in col_idx:
            new_col = df.iloc[:, j].copy() #instantiate a copy of this column which will be used to replace the existing one in new_df
            if self.num_format == -1 or self.num_format > len(self.formats):
                subformats = self.formats #use all formats
            else:
                subformats = rng.choice(self.formats, size=self.num_format, replace=False) #randomly select num_format formats from self.formats to be used for this column
            
            date_formats_used[j] = list(subformats)

            random_idxs = np.array_split(rng.choice(nrow, size=nrow, replace=False), len(subformats)) #randomly split dataframe indices into len(subformats) number of groups
            
            for i in range(len(subformats)): #for each group of indices, apply a different format from subformats
                new_col.iloc[random_idxs[i]] = new_df.iloc[random_idxs[i], j].apply(lambda x: x if pd.isna(x) else x.strftime(subformats[i]))
                #for each set of random indices, apply a different strftime format

            new_df.iloc[:, j] = new_col

        end = time()
        message += {new_df.columns[k]: v for k, v in date_formats_used.items()}.__repr__()
        self.update_history(message, end - start)
        return new_df, {}, {}

class DateFormatStainer(DatetimeFormatStainer):
    """Stainer to alter the format of dates for given date columns.

    Subclass of DatetimeFormatStainer.
    """
    #: Set as "date" - only datetime/date columns will be selected for reformatting
    col_type = "date"

    def __init__(self, name="Date Formats", col_idx = [], num_format = 2, formats = None):
        """The constructor for DateFormatStainer class.  
        
        Parameters
        ----------
        name : str, optional
            Name of stainer. Default is "Date Formats".
        col_idx : int list, optional
            Column indices that the stainer will operate on. Default is empty list.
        num_format : int, optional
            Number of date formats present within each column. If num_format > number of available formats, 
            or num_format == -1, use all formats. Default is 2.
        formats : str list or None, optional
            List of date string format options that the DateFormatStainer chooses from. Use datetime module string formats (e.g. '%d%b%Y'). 
            If None, a default list of 41 non-ambiguous (month is named) date formats are provided. Default is None.
        """
        if formats == None:
            formats = [f"{dm_y[0]}{br}{dm_y[1]}" for br in [",", ", ", "-", "/", " "]
                        for m_type in ["%b", "%B"]
                        for d_m in itertools.permutations(["%d", m_type])
                        for d_m_str in [f"{d_m[0]}{br}{d_m[1]}"]
                        for dm_y in itertools.permutations([d_m_str, '%Y'])
                    ] + ['%Y%m%d'] #default formats; 41 total and non-ambiguous

        super().__init__(col_idx=col_idx, name=name, num_format=num_format, formats=formats)


class DatetimeSplitStainer(Stainer):
    """Stainer that splits each given date / datetime columns into 3 columns respectively, representing day, month, and year.

    If a given column's name is 'X', then the respective generated column names are 'X_day', 'X_month', and 'X_year'. If keep_time is True,
    then further generate 'X_hour', 'X_minute', and 'X_second'. Otherwise, only dates will be kept.

    If a column is split, the original column will be dropped.

    For 'X_month' and 'X_year', a format from ['m', '%B', '%b'], and ['%Y', '%y'] is randomly chosen respectively.  
    """
    #: Set as "datetime" - only datetime/date/time columns will be selected for splitting
    col_type = "datetime"

    def __init__(self, name="Datetime Split", col_idx = [], keep_time = True, prob=1.0):
        """The constructor for DatetimeSplitStainer class.  
        
        Parameters
        ----------
        name : str, optional
            Name of stainer. Default is "Datetime Split".
        col_idx : int list, optional
            Column indices that the stainer will operate on. Default is empty list.
        keep_time : boolean, optional
            Whether time component of datetime should be kept, thus 3 new columns are created. Default is True.
        prob : float [0, 1], optional
            Probability that the stainer splits a date column. Probabilities of split for each given date column are independent. Default is 1.
        """
        super().__init__(name, [], col_idx)
        self.keep_time = keep_time

        if prob < 0 or prob > 1:
            raise ValueError("prob is a probability, it must be in the range [0, 1].")
        else:
            self.prob = prob
        
    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.

        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter as this stainer does not use row indices.
        col_idx : int list, optional
            Column indices that the stainer will operate on. Will take priority over the class attribute `col_idx`.
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : dictionary {int: int}
            Column mapping showing the relationship between the original and new column positions.
        """
        new_df, row_idx, col_idx = self._init_transform(df, row_idx, col_idx)
        start = time()
        
        message = f"Split the following date columns: "
        
        col_map_dct = {j: [] for j in range(df.shape[1])} #initialize column map dictionary; new number of columns is unknown at start.
        j_new = 0 #running column index for output df

        #iterate over all columns, and apply logic only when current column index is in self.col_idx
        for j in range(df.shape[1]):
            if (j not in col_idx) or (rng.random() > self.prob): #current column index not in self.col_idx, or no split due to probability
                col_map_dct[j].append(j_new)
                j_new += 1
            else:
                col_name = df.columns[j]
                message += f"{col_name}, "
                
                #check to ensure no undetected column name conflict
                if f"{col_name}_day" in new_df.columns:
                    raise KeyError(f"column name: '{col_name}_day' already exists in dataframe.")
                if f"{col_name}_month" in new_df.columns:
                    raise KeyError(f"column name: '{col_name}_month' already exists in dataframe.")
                if f"{col_name}_year" in new_df.columns:
                    raise KeyError(f"column name: '{col_name}_year' already exists in dataframe.")
                
                month_format = rng.choice(["%m", "%B", "%b"]) #randomly chosen month format
                year_format = rng.choice(["%Y", "%y"]) #randomly chosen year format

                new_df.drop(col_name, axis=1, inplace=True)
                new_df.insert(j_new, f"{col_name}_day", df[col_name].apply(lambda x: x if pd.isna(x) else x.strftime("%d")))
                new_df.insert(j_new + 1, f"{col_name}_month", df[col_name].apply(lambda x: x if pd.isna(x) else x.strftime(month_format)))
                new_df.insert(j_new + 2, f"{col_name}_year", df[col_name].apply(lambda x: x if pd.isna(x) else x.strftime(year_format)))
                
                col_map_dct[j].extend([j_new, j_new + 1, j_new + 2])
                j_new += 3

                if self.keep_time:
                    #check to ensure no undetected column name conflict
                    if f"{col_name}_hour" in new_df.columns:
                        raise KeyError(f"column name: '{col_name}_hour' already exists in dataframe.")
                    if f"{col_name}_minute" in new_df.columns:
                        raise KeyError(f"column name: '{col_name}_minute' already exists in dataframe.")
                    if f"{col_name}_second" in new_df.columns:
                        raise KeyError(f"column name: '{col_name}_second' already exists in dataframe.")

                    new_df.insert(j_new, f"{col_name}_hour", df[col_name].apply(lambda x: x if pd.isna(x) else x.strftime("%H")))
                    new_df.insert(j_new + 1, f"{col_name}_minute", df[col_name].apply(lambda x: x if pd.isna(x) else x.strftime("%M")))
                    new_df.insert(j_new + 2, f"{col_name}_second", df[col_name].apply(lambda x: x if pd.isna(x) else x.strftime("%S")))
                    
                    col_map_dct[j].extend([j_new, j_new + 1, j_new + 2])
                    j_new += 3

        if j == j_new - 1:
            message = "No date columns were split."
        else:
            message = message[:-2]

        end = time()
        self.update_history(message, end - start)
        return new_df, {}, col_map_dct
    
class FTransformStainer(Stainer):
    """
    Stainer that takes a numerical column and applies a transformation to it. Only works on numerical columns. 
    If any other column is selected, a type error will be raised.
    """
    #: Set as "numeric" - only numeric columns will be selected for transformation
    col_type = "numeric"
    #: 7 default functions, namely square, cube, sqrt (square root), cubert (cube root), inverse (1/x), ln (natural logarithm), exp (exponential)
    function_dict = {"square": lambda x: x**2,
                 "cube": lambda x: x**3,
                 "sqrt": lambda x: round(x**0.5, 2),
                 "cubert": lambda x: round(x**(1/3), 2),
                 "inverse": lambda x: 1000 if x == 0 else round(1/x, 2),
                 "ln": lambda x: 0 if x == 0 else round(np.log(x), 2),
                 "exp": lambda x: round(np.exp(x), 2)}
    
    def __init__(self, deg, name = "Function Transform", col_idx = [], trans_lst = [], trans_dict = {}, scale = False):
        """
        The constructor for FTransformStainer class.  
        
        Parameters
        ----------
        deg : float (0, 1]
            Determines the proportion of selected data that would be transformed
        name : str, optional
            Name of stainer. Default is "Function Transform"
        col_idx : int list, optional
            Column indices that the stainer will operate on. Default is empty list.
        trans_lst : str list, optional
            Names of transformations in function_dict to include in the pool of possible transformations. Default is empty list.
        trans_dict : {str : function} dictionary, optional
            {Name of transformation: Function} to include in the pool of possible transformations. 
            
            Default is empty dictionary. If no transformation has been selected, all default functions will be selected instead.
        scale : boolean
            If True, will scale the data back to its original range. 
            Defaults to False
            
        Raises
        ----------
        ValueError
            Degree provided is not in the range of (0, 1]
        Exception
            If multiple functions are given the same name
        NameError
            Name provided in trans_lst is not one of the 7 default transformations
        TypeError
            Invalid column type provided 
        ZeroDivisionError
            Transformation would reuslt in division by zero
        """
        super().__init__(name, [], col_idx)
        if deg <= 0 or deg > 1:
            raise ValueError("Degree should be in range (0, 1]")
        self.deg = deg
        self.trans = trans_dict.copy()
        for label in trans_lst:
            if label in self.trans:
                raise Exception(f"Duplicate Function Name: {label}")
            try:
                self.trans[label] = self.function_dict[label]
            except:
                raise NameError(f"Invalid Transformation Name: {label}")
        if len(self.trans) == 0:
            self.trans = FTransformStainer.function_dict 
        self.scale = scale
    
    def transform(self, df, rng, row_idx, col_idx):
        """Applies staining on the given indices in the provided dataframe.
        
        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter as this stainer does not use row indices. All rows within the selected columns will be transformed.
        col_idx : int list, optional
            Column indices that the stainer will operate on. Will take priority over the class attribute `col_idx`.
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : empty dictionary
            This stainer does not produce any column mappings.
        """
        new_df, _, cols = self._init_transform(df, row_idx, col_idx)
        start = time()
        
        rando_idx = rng.choice(len(cols), int(len(cols) * self.deg), replace = False)
        message = ""
        
        for idx in rando_idx:
            col = cols[idx]
            try:
                orig_min = new_df.iloc[:, col].min()
                orig_max = new_df.iloc[:, col].max()

                rando_func = rng.choice(list(self.trans.keys()))

                new_df.iloc[:, col] = new_df.iloc[:, col].apply(self.trans[rando_func])

                if self.scale:
                    curr_col = new_df.iloc[:, col]
                    data_min, data_max = curr_col.min(), curr_col.max()
                    std_dev = (curr_col - data_min) / (data_max - data_min)
                    new_col = std_dev * (orig_max - orig_min) + orig_min
                    new_df.iloc[:, col] = new_col
                    
            except TypeError:
                raise TypeError(f"Column '{new_df.columns[col]}' is invalid column for numerical transformation")
            except ZeroDivisionError:
                raise ZeroDivisionError(f"Applying {rando_func} on {new_df.columns[col]} results in a division by zero.")
            
            message += f"Converted column {new_df.columns[col]} with transformation {rando_func}. \n "
        
        end = time()
        self.update_history(message, end - start)
        return new_df, {}, {}
    
class NullifyStainer(Stainer):
    """
    Stainer that convert various values to missing data / values that represent missing values.
    """
    
    def __init__(self, deg, name = "Nullify", row_idx = [], col_idx = [], new_val = None, new_type = False):
        """ The constructor for NullifyStainer class.  
        
        Parameters
        ----------
        deg : float (0, 1]
            Determines the proportion of selected data that would be nullified
        name : str, optional 
            Name of stainer. Default is "Nullify"
        row_idx : int list, optional
            Indices of rows which will be considered for transformation (depending on the degree). Default is empty list
        col_idx : int list, optional
            Indices of columns which will be considered for transformation (depending on the degree). Default is empty list
        new_val : any, optional
            Value that would replace the specific data. Defaults to None
        new_type : boolean, optional
            Allows the new_val to be of a different type than the current column.
            
            Defaults to False (new_val must be same type as the column to be changed)
            
        Raises
        ----------
        ValueError
            Degree provided is not in the range of (0, 1]
        TypeError
            Only when new_type is set to False. Denotes column type is being changed via the addition of the new_val.
        """
        super().__init__(name, row_idx, col_idx)
        if deg <= 0 or deg > 1:
            raise ValueError("Degree should be in range (0, 1]")
        self.deg = deg
        self.new_val = new_val
        self.new_type = new_type
        
    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.
        
        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Row indices that the stainer will operate on.
        col_idx : int list, optional
            Column indices that the stainer will operate on. 
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : empty dictionary
            This stainer does not produce any column mappings.
        """
        new_df, row, col = self._init_transform(df, row_idx, col_idx)
        start = time()
        
        all_cells = list(product(row, col))
        total_null = int(len(all_cells) * self.deg)
        selected_cells = rng.choice(len(all_cells), size = total_null, replace = False)

        for idx in selected_cells:
            row, col = all_cells[idx]
            if self.new_val != None and \
            is_categorical_dtype(new_df.iloc[:, col]) and \
            self.new_val not in new_df.iloc[:, col].cat.categories:
                new_df.iloc[:, col] = new_df.iloc[:, col].cat.add_categories(self.new_val)
            new_df.iloc[row, col] = self.new_val
        
        if self.new_val != None and not self.new_type:
            if np.mean(df.dtypes == new_df.dtypes) < 1:
                raise TypeError(f"Column type changed when nullifying for: {df.columns[(df.dtypes != new_df.dtypes)].tolist()}")
        
        end = time()
        message = f"Replaced {total_null} values to become {'empty' if self.new_val == None else self.new_val} in specificed rows/cols."
        self.update_history(message, end - start)
        
        return new_df, {}, {}

class BinningStainer(Stainer):
    """
    Stainer that bins continuous columns into discrete groups (each group represents an interval [a,b)).
    """
    #:  Set as "numeric" - only numeric columns will be selected for binning
    col_type = "numeric"

    def __init__(self, name="Binning", col_idx=[], group_size=None, n_groups=5, sf=4):
        """The constructor for BinningStainer class.  
        
        Parameters
        ----------
        name : str, optional
            Name of stainer. Default is "Binning".
        col_idx : int list, optional
            Column indices that the stainer will operate on. Default is empty list.
        group_size : int or None, optional
            Number of elements in each interval group. If None, then uses n_groups. Default is None.
        n_groups : int, optional
            Number of interval groups to bin to. Ignored if group_size is not None. Default is 5.
        sf : int
            Number of significant digits to be used in the output string representation for the intervals.
        """
        super().__init__(name, [], col_idx)
        self.type = type
        self.range = range
        self.group_size = group_size
        self.n_groups = n_groups
        self.sf = sf
    
    @staticmethod
    def _bin_into_group(x, cutpoints):
        """Helper to bin decimal into the correct group.

        Parameters
        ----------
        x : numeric
            value to bin into a group.
        cutpoints : numeric list
            the various cutpoints which define the groups.
        """
        #binary search for upper bound index, which is 'high'
        low=0
        high=len(cutpoints)-1
        while low < high:
            mid = low + (high - low) // 2
            if x < cutpoints[mid]:
                high = mid
            else:
                low = mid + 1

        lower_bound = cutpoints[high - 1]
        upper_bound = cutpoints[high]

        if high == len(cutpoints) - 1: #last index, closed interval
            return f"[{lower_bound}, {upper_bound}]"
        else: #not last index, half-open interval
            return f"[{lower_bound}, {upper_bound})"


    def transform(self, df, rng, row_idx=None, col_idx=None):
        """Applies staining on the given indices in the provided dataframe.

        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter as this stainer does not use row indices.
        col_idx : int list, optional
            Column indices that the stainer will operate on. Will take priority over the class attribute `col_idx`.
        
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : empty dictionary
            This stainer does not produce any column mappings.
        """
        new_df, row_idx, col_idx = self._init_transform(df, row_idx, col_idx)

        start = time()
        message = "Binning using the following cutpoints:\n"
        cutpoints_used = {} #dict of cutpoints used per column

        #helper function to round to significant digits
        def round_sig(x, sig=2):
            return round(x, sig-int(np.floor(np.log10(abs(x))))-1)

        #iterate over each column index
        for j in col_idx:
            new_col = df.iloc[:, j].copy() #instantiate a copy of this column which will be used to replace the existing one in new_df

            if self.group_size:
                n_groups = new_col.shape[0] // self.group_size
            else:
                n_groups = self.n_groups
            
            cutpoints = [round_sig(cp, self.sf) for cp in new_col.quantile([i/n_groups for i in range(n_groups + 1)], interpolation='lower').tolist()]
            cutpoints_used[j] = cutpoints

            new_df.iloc[:, j] = new_col.apply(lambda x: x if pd.isna(x) else self._bin_into_group(x, cutpoints))
        
        end = time()
        
        message += {new_df.columns[k]: v for k, v in cutpoints_used.items()}.__repr__()
        self.update_history(message, end - start)
        return new_df, {}, {}

      
from ddf.latlong import Latlong

class LatlongFormatStainer(Stainer):
    """
    Stainer to alter the format of datetimes for given latlong columns.
    """
    
    
    def __init__(self, col_idx, name="Latlong Formats", num_format = 2, formats = None):
        """ Constructor for LatlongFormatStainer
        
        Parameters
        ----------
        col_idx : int list
            Columns to perform latlong stainer on.
        name : str, optional
            Name of stainer. Default is LatlongFormats
        num_format : int, optional
            Number of latlong formats present within each column. If num_format > number of available formats, or num_format == -1, use all formats. 
            Defaults to 2.
        formats : str list or None, optional
            List of latlong string format options that the LatlongFormatStainer chooses from. Use the Latlong module string formats. 
            If None, a default list of formats are provided.
            Defaults to None.
        """
        
        super().__init__(name, [], col_idx)
        self.num_format = num_format

        if formats:
            self.formats = formats
        else:
            self.formats = ['DMS', 'MinDec'] #default formats
            
        
    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.

        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter as this stainer does not use row indices. 
        col_idx : int list, optional
            Column indices that the stainer will operate on.
            
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : empty dictionary
            This stainer does not produce any column mappings.
        """
        new_df, row_idx, col_idx = self._init_transform(df, row_idx, col_idx)

        start = time()
        nrow = new_df.shape[0]
        message = "Latlong Formats used:\n"
        latlong_formats_used = {} #dict to store latlong formats used
        
        #iterate over each column index
        for j in col_idx:
            new_col = df.iloc[:, j].copy() #instantiate a copy of this column which will be used to replace the existing one in new_df
            if self.num_format == -1 or self.num_format > len(self.formats):
                subformats = self.formats #use all formats
            else:
                subformats = rng.choice(self.formats, size=self.num_format, replace=False) #randomly select num_format formats from self.formats to be used for this column
            
            latlong_formats_used[j] = list(subformats)
            random_idxs = np.array_split(rng.choice(nrow, size=nrow, replace=False), len(subformats)) #randomly split dataframe indices into len(subformats) number of groups
            
            for i in range(len(subformats)): #for each group of indices, apply a different format from subformats
                new_col.iloc[random_idxs[i]] = new_df.iloc[random_idxs[i], j].apply(lambda x: x if pd.isna(x) else x.strflatlong(subformats[i]))
                #for each set of random indices, apply a different latlong format

            new_df.iloc[:, j] = new_col
    
        end = time()
        message += {new_df.columns[k]: v for k, v in latlong_formats_used.items()}.__repr__()
        self.update_history(message, end - start)
        return new_df, {}, {}


class LatlongSplitStainer(Stainer):
    """
    Stainer that splits each given latlong columns into 6 columns, representing degree, minute, and seconds, for lat and long respectively.
    If a given column's name is 'X', then the respective generated column names 'X_lat_deg', 'X_lat_min', 'X_lat_sec', 'X_long_deg', 'X_long_min',
    and 'X_long_sec'.
    If a column is split, the original column will be dropped.
    """
    def __init__(self, col_idx, name="Latlong Split", prob=1.0):
        """ Constructor for LatlongSplitStainer
        
        Parameters
        ----------
        col_idx : int list
            latlong columns to perform latlong splitting on.
        name : str, optional
            Name of stainer. Default is Latlong Split. 
        prob : float [0, 1], optional
            probability that the stainer splits a latlong column. Probabilities of split for each given date column are independent.
            Defaults to 1.
            
        Raises
        ----------
        ValueError:
            Probability provided is not in the range of [0, 1]
        """
        super().__init__(name, [], col_idx)

        if prob < 0 or prob > 1:
            raise ValueError("prob is a probability, it must be in the range [0, 1].")
        else:
            self.prob = prob
        
    def transform(self, df, rng, row_idx = None, col_idx = None):
        """Applies staining on the given indices in the provided dataframe.

        Parameters
        ----------
        df : pd.DataFrame 
            Dataframe to be transformed.
        rng : np.random.BitGenerator
            PCG64 pseudo-random number generator.
        row_idx : int list, optional
            Unused parameter as this stainer does not use row indices. 
        col_idx : int list, optional
            Column indices that the stainer will operate on.
            
        Returns
        -------
        new_df : pd.DataFrame
            Modified dataframe.
        row_map : empty dictionary
            This stainer does not produce any row mappings.
        col_map : empty dictionary
            Column mapping showing the relationship between the original and new column positions.
        """
        new_df, row_idx, col_idx = self._init_transform(df, row_idx, col_idx)

        start = time()
        
        message = f"Split the following latlong columns: "
        
        col_map_dct = {j: [] for j in range(df.shape[1])} #initialize column map dictionary; new number of columns is unknown at start.
        j_new = 0 #running column index for output df

        #iterate over all columns, and apply logic only when current column index is in self.col_idx
        for j in range(df.shape[1]):
            if (j not in self.col_idx) or (rng.random() > self.prob): #current column index not in self.col_idx, or no split due to probability
                col_map_dct[j].append(j_new)
                j_new += 1
            else:
                col_name = df.columns[j]
                message += f"{col_name}, "
                
                #check to ensure no undetected column name conflict
                for suffix in ['lat_deg', 'lat_min', 'lat_sec', 'long_deg', 'long_min', 'long_sec']:
                    if f"{col_name}_{suffix}" in new_df.columns:
                        raise KeyError(f"column name: '{col_name}_{suffix}' already exists in dataframe.")

                new_df.drop(col_name, axis=1, inplace=True)
                new_df.insert(j_new, f"{col_name}_lat_deg", df[col_name].apply(lambda x: x if pd.isna(x) else x.strflatlong("%da")))
                new_df.insert(j_new + 1, f"{col_name}_lat_min", df[col_name].apply(lambda x: x if pd.isna(x) else x.strflatlong("%ma")))
                new_df.insert(j_new + 2, f"{col_name}_lat_sec", df[col_name].apply(lambda x: x if pd.isna(x) else x.strflatlong("%s5a")))
                new_df.insert(j_new + 3, f"{col_name}_long_deg", df[col_name].apply(lambda x: x if pd.isna(x) else x.strflatlong("%do")))
                new_df.insert(j_new + 4, f"{col_name}_long_min", df[col_name].apply(lambda x: x if pd.isna(x) else x.strflatlong("%mo")))
                new_df.insert(j_new + 5, f"{col_name}_long_sec", df[col_name].apply(lambda x: x if pd.isna(x) else x.strflatlong("%s5o")))
                
                col_map_dct[j].extend([j_new, j_new + 1, j_new + 2, j_new + 3, j_new + 4, j_new + 5])
                j_new += 6
        
        if j == j_new - 1:
            message = "No latlong columns were split."
        else:
            message = message[:-2]

        end = time()
        self.update_history(message, end - start)
        return new_df, {}, col_map_dct
