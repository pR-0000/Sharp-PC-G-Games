"""FR/EN: Star Lane's native five-lane G850 edition."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from g850_machine import G850Machine
from check_star import StarChecks
class StarG850(G850Machine):
    def __init__(self,language='FR'):
        self.language=language
        super().__init__('star_lane_g850_'+language,HERE/'build/g850')
class NativeChecks(StarChecks):
    machine_class=StarG850
if __name__=='__main__':
    from cli_i18n import Parser
    Parser('Verifier la version G850.','Check the G850 edition.').parse_args()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeChecks)).wasSuccessful())
