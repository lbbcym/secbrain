# Mutmut Configuration for SecBrain
# Mutation testing verifies the quality of test suites by introducing bugs
# Documentation: https://mutmut.readthedocs.io/

[mutmut]
# Paths to mutate
paths_to_mutate = secbrain/

# Paths to exclude from mutation
paths_to_exclude = 
    secbrain/tests/
    secbrain/examples/
    secbrain/__pycache__/

# Test command to run after each mutation
runner = pytest -x -q

# Test discovery pattern
tests_dir = secbrain/tests/

# Additional options
# dict_synonyms = synonyms.txt  # Optional: file with synonym replacements

# Backup directory for mutated files
# backup_dir = .mutmut-cache

# Use coverage to guide mutation (only mutate covered lines)
# use_coverage = True
# coverage_data = .coverage

# Experimental features
# use_patch_file = mutants.patch
