from constants import DEBUGGING, DEBUG_ENV

def _getDebugDescription():
    return "(debug=" + str(DEBUG_ENV) + ")"
debug_description = _getDebugDescription()

def _getAppTitle():
    name = "VocabSieve"
    if DEBUGGING: 
        return name + " " + debug_description
    else:
        return name
app_title = _getAppTitle()
app_organization = "FreeLanguageTools"

lookup_placeholder = 'Look up a word by double clicking it. Or, select it, then press "Get definition".'
lookup_tooltip = 'Look up a word by double clicking it. Or, select it,\nthen press "Get definition".'
lookup_loading = 'Looking up word...'
