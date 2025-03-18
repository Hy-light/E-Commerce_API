# get current host function
def get_current_host(request):
    protocol = request.is_secure() and 'https' or 'http'
    host = request.get_host()
    return f'{protocol}://{host}/'.format(host=host, protocol=protocol)

