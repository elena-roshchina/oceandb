function toggleDisplay(ident)
    {
      var e = document.getElementById(ident);
      if (!e.style.saved_display)
      {
          e.style.saved_display = ''
      }
      if (e.style.display == 'none')
      {
        e.style.display = e.style.saved_display;
      }
      else
      {
        e.style.saved_display = e.style.display;
        e.style.display = 'none'
      };
    } // end of function toggleDisplay