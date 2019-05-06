Option('specializer',
       'use specializing interpreter',
       short_name='O',
       top_level_code='#include "mit/specializer.h"',
       parse_code='run_fn = mit_run_specialized;',
)
