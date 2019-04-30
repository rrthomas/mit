Option('specializer',
       'use specializing interpreter',
       short_name='O',
       top_level_code='#include "smite/specializer.h"',
       parse_code='run_fn = smite_run_specialized;',
)
