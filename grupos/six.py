from treebeard.al_tree import get_result_class

__doc__ = '''
    Con este módulo se pretende extender el uso de la clase AL_Node que tiene la clase de Grupo,
    añadiendo los querysets que incluyen grupos de todos los estados, con el fin de mantener registros
    de los grupos que no se encuentran en estado activo.
'''

__author__ = 'German Alzate'


__all__ = ['SixALNode']


class SixALNode(object):
    """
    Clase para mantener la compatibilidad con AL_Node.
    Se crea con el objetivo de sobreescribir metodos y mantener el funcionamiento
    original de la clase.
    """

    @property
    def _grupos_red(self):
        """
        Metodo para mantener la compatibilidad con modelo de grupos, devolviendo
        todos los grupos de la red incluyendo los archivados.

        :returns: Un QuerySet con la lista de los grupos del arbol dado el padre,
                  incluye a los grupos en estado inactivo.
        """
        from .utils import convertir_lista_grupos_a_queryset
        return convertir_lista_grupos_a_queryset(self._get_tree(self))

    @classmethod
    def _get_root_nodes(cls):
        """:returns: A queryset containing the root nodes in the tree."""
        return get_result_class(cls)._default_manager.filter(parent__isnull=True)

    def _get_children(self):
        """:returns: A queryset of all the node's children"""
        return get_result_class(self.__class__)._default_manager.filter(parent=self)

    def _get_ancestors(self):
        """
        :returns: A *list* containing the current node object's ancestors,
                  starting by the root node and descending to the parent.
        """
        ancestors = []
        if self._meta.proxy_for_model:
            # the current node is a proxy model; our result set
            # should use the same proxy model, so we need to
            # explicitly fetch instances of that model
            # when following the 'parent' relation
            cls = self.__class__
            node = self
            while node.parent_id:
                node = cls._default_manager.get(pk=node.parent_id)
                ancestors.insert(0, node)
        else:
            node = self.parent
            while node:
                ancestors.insert(0, node)
                node = node.parent
        return ancestors

    @classmethod
    def _dump_bulk(cls, parent=None, keep_ids=True):
        """Dumps a tree branch to a python data structure."""

        serializable_cls = cls._get_serializable_model()
        if (
                parent and serializable_cls != cls and
                parent.__class__ != serializable_cls
        ):
            parent = serializable_cls._default_manager.get(pk=parent.pk)

        # a list of nodes: not really a queryset, but it works
        objs = serializable_cls._get_tree(parent)

        ret, lnk = [], {}
        for node, pyobj in zip(objs, serializers.serialize('python', objs)):
            depth = node.get_depth()
            # django's serializer stores the attributes in 'fields'
            fields = pyobj['fields']
            del fields['parent']

            # non-sorted trees have this
            if 'sib_order' in fields:
                del fields['sib_order']

            if 'id' in fields:
                del fields['id']

            newobj = {'data': fields}
            if keep_ids:
                newobj['id'] = pyobj['pk']

            if (not parent and depth == 1) or\
               (parent and depth == parent.get_depth()):
                ret.append(newobj)
            else:
                parentobj = lnk[node.parent_id]
                if 'children' not in parentobj:
                    parentobj['children'] = []
                parentobj['children'].append(newobj)
            lnk[node.pk] = newobj
        return ret

    @classmethod
    def __get_tree_recursively(cls, results, parent, depth):
        if parent:
            nodes = parent._get_children()
        else:
            nodes = cls._get_root_nodes()
        for node in nodes:
            node._cached_depth = depth
            results.append(node)
            cls.__get_tree_recursively(results, node, depth + 1)

    @classmethod
    def _get_tree(cls, parent=None):
        """
        :returns: A list of nodes ordered as DFS, including the parent. If
                  no parent is given, the entire tree is returned.
        """
        if parent:
            depth = parent.get_depth() + 1
            results = [parent]
        else:
            depth = 1
            results = []
        cls.__get_tree_recursively(results, parent, depth)
        return results

    def _get_siblings(self):
        """
        :returns: A queryset of all the node's siblings, including the node
                  itself.
        """
        if self.parent:
            return get_result_class(self.__class__)._default_manager.filter(
                parent=self.parent)
        return self.__class__._get_root_nodes()
