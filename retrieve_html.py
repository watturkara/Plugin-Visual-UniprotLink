def retrieve_html(html_link):
    """
    Open an html file and read in the html
    
    Requirements
    -------
    None
    
    Parameters
    ----------
    html_link : string
        the name of the html file to read in, e.g. f'{cwd}//bar_graph.html'
        
    Returns
    -------
    read_html: string
        the html read out of the file
   
    Example
    --------
    import os
    cwd = os.getcwd()
    
    filename = os.path.join(cwd, 'bar_graph.html')
    
    read_html = retrieve_html(filename)
    
    Output:
        <html>
            <body>
                <div>
                     <script type="text/javascript">window.PlotlyConfig = {MathJaxConfig: 'local'};</script>
                </div>
            </body>
         </html>
    """    
    
    #open the htmllink file
    fl = open(html_link, "r")
    
    #read in the html
    read_html = fl.read()
    
    return (read_html)
