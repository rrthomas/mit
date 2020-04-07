((latex-mode . ((eval . (add-hook 'after-save-hook
                                  (lambda () (TeX-command-menu "LaTeX make"))
                                  nil t)))))
